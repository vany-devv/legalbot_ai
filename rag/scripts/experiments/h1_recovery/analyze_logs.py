"""H1 — анализ результатов прогонов и формирование отчёта.

Считает:
  - actual_rate = (parse_path != total_failure в run A) / N
  - baseline_rate = (parse_path == json_loads_ok в run B) / N
  - lift = actual_rate − baseline_rate (изолирует эффект recovery)
  - recovery_rate = доля битых raw (json.loads падает в B), которые recovery
    восстановил в A (parse_path != total_failure)
  - Wilson 95% CI для actual и baseline
  - h0_rejected = (lift >= 0.25) AND (recovery_rate >= 0.90)

Сохраняет:
  - reports/report.json
  - reports/report.md
  - reports/chart_h1_parse_paths.png
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
from collections import Counter
from pathlib import Path

from statsmodels.stats.proportion import proportion_confint
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).parent
REPORTS_DIR = ROOT / "reports"
RUN_A = REPORTS_DIR / "runA.jsonl"
RUN_B = REPORTS_DIR / "runB.jsonl"

THRESHOLD_LIFT = 0.25
THRESHOLD_RECOVERY_RATE = 0.90


def load_run(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def get_commit_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, cwd=ROOT,
        ).strip()
    except Exception:
        return "unknown"


def main() -> None:
    run_a = load_run(RUN_A)
    run_b = load_run(RUN_B)
    n = len(run_a)
    if n == 0 or n != len(run_b):
        raise SystemExit(f"Несбалансированные прогоны: {len(run_a)} vs {len(run_b)}")

    # Сводки
    counter_a = Counter(r["parse_path"] for r in run_a)
    counter_b = Counter(r["parse_path"] for r in run_b)

    successful_a = sum(c for path, c in counter_a.items() if path != "total_failure")
    json_loads_b = counter_b.get("json_loads_ok", 0)

    actual_rate = successful_a / n
    baseline_rate = json_loads_b / n
    lift = actual_rate - baseline_rate

    # recovery_rate: для material_id, где json.loads падает в B (parse_path != json_loads_ok),
    # смотрим parse_path в A. Если != total_failure — recovery восстановил.
    a_by_id = {r["material_id"]: r["parse_path"] for r in run_a}
    b_by_id = {r["material_id"]: r["parse_path"] for r in run_b}
    problematic_ids = [mid for mid, p in b_by_id.items() if p != "json_loads_ok"]
    recovered_ids = [mid for mid in problematic_ids
                     if a_by_id.get(mid, "total_failure") != "total_failure"]
    recovery_rate = len(recovered_ids) / len(problematic_ids) if problematic_ids else 0.0

    # Wilson 95% CI
    a_low, a_high = proportion_confint(successful_a, n, alpha=0.05, method="wilson")
    b_low, b_high = proportion_confint(json_loads_b, n, alpha=0.05, method="wilson")

    cond_lift = lift >= THRESHOLD_LIFT
    cond_recovery = recovery_rate >= THRESHOLD_RECOVERY_RATE
    h0_rejected = cond_lift and cond_recovery

    report = {
        "n": n,
        "actual_rate": round(actual_rate, 4),
        "actual_ci_low": round(a_low, 4),
        "actual_ci_high": round(a_high, 4),
        "baseline_rate": round(baseline_rate, 4),
        "baseline_ci_low": round(b_low, 4),
        "baseline_ci_high": round(b_high, 4),
        "lift": round(lift, 4),
        "n_problematic": len(problematic_ids),
        "n_recovered": len(recovered_ids),
        "recovery_rate": round(recovery_rate, 4),
        "threshold_lift": THRESHOLD_LIFT,
        "threshold_recovery_rate": THRESHOLD_RECOVERY_RATE,
        "conditions": {
            "lift_ge_threshold": cond_lift,
            "recovery_rate_ge_threshold": cond_recovery,
        },
        "h0_rejected": h0_rejected,
        "parse_path_distribution_A": dict(counter_a),
        "parse_path_distribution_B": dict(counter_b),
        "env_snapshot": {
            "commit_hash": get_commit_hash(),
            "python_version": os.popen("python3 --version").read().strip(),
            "model_provider": "GigaChat-Pro",
            "embedder_model": "Yandex-256",
            "corpus_size": n,
            "started_at": "see runs in jsonl",
            "finished_at": dt.datetime.now().isoformat(timespec="seconds"),
        },
    }

    (REPORTS_DIR / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    # === Markdown-отчёт ===
    md_lines = [
        "# H1 — устойчивость парсинга json: результаты",
        "",
        f"Корпус: {n} сырых ответов модели.",
        "",
        "## Метрики",
        "",
        f"- actual_rate (recovery on): **{actual_rate:.3f}** "
        f"(95% CI [{a_low:.3f}, {a_high:.3f}])",
        f"- baseline_rate (recovery off): **{baseline_rate:.3f}** "
        f"(95% CI [{b_low:.3f}, {b_high:.3f}])",
        f"- lift = actual − baseline: **{lift:.3f}** ({lift*100:.1f} п.п.)",
        f"- recovery_rate (битых raw восстановлено): "
        f"**{len(recovered_ids)} из {len(problematic_ids)} = {recovery_rate:.3f}**",
        "",
        "## Условия отвержения H₀",
        "",
        f"1. lift ≥ {THRESHOLD_LIFT}: **{'выполнено' if cond_lift else 'не выполнено'}**",
        f"2. recovery_rate ≥ {THRESHOLD_RECOVERY_RATE}: "
        f"**{'выполнено' if cond_recovery else 'не выполнено'}**",
        "",
        f"H₀ отвергается: **{'ДА' if h0_rejected else 'НЕТ'}**",
        "",
        "## Распределение parse_path",
        "",
        "| Путь | Run A (recovery on) | Run B (recovery off) |",
        "|---|---|---|",
    ]
    all_paths = sorted(set(counter_a.keys()) | set(counter_b.keys()))
    for p in all_paths:
        md_lines.append(f"| {p} | {counter_a.get(p, 0)} | {counter_b.get(p, 0)} |")
    md_lines.append("")
    md_lines.append("## Обсуждение")
    md_lines.append("")
    if h0_rejected:
        md_lines.append(
            f"Recovery-механизм даёт значимый прирост над baseline ({lift*100:.1f} п.п.) "
            f"и восстанавливает {recovery_rate*100:.1f}% битых raw в валидную структуру. "
            "Оба условия отвержения H₀ выполнены, гипотеза H1 подтверждена."
        )
    else:
        md_lines.append(
            "H₀ не отвергнута. Либо прирост над baseline меньше 25 п.п. (эффект recovery "
            "не достигает порога значимости), либо доля восстановленных битых raw меньше 90% "
            "(recovery не покрывает значимую часть наблюдаемых паттернов поломок). "
            "Для интерпретации см. распределение parse_path и detailed-таблицу выше."
        )

    (REPORTS_DIR / "report.md").write_text("\n".join(md_lines), encoding="utf-8")

    # === График ===
    fig, ax = plt.subplots(figsize=(8, 5))
    paths = all_paths
    a_vals = [counter_a.get(p, 0) for p in paths]
    b_vals = [counter_b.get(p, 0) for p in paths]
    x = range(len(paths))
    width = 0.35
    ax.bar([i - width / 2 for i in x], a_vals, width, label="Run A (recovery on)")
    ax.bar([i + width / 2 for i in x], b_vals, width, label="Run B (recovery off)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(paths, rotation=20, ha="right")
    ax.set_ylabel("Количество")
    ax.set_title("Распределение parse_path: A vs B")
    ax.legend()
    fig.tight_layout()
    fig.savefig(REPORTS_DIR / "chart_h1_parse_paths.png", dpi=120)
    plt.close(fig)

    print(f"Сохранено: {REPORTS_DIR}/report.json, report.md, chart_h1_parse_paths.png")
    print(f"actual={actual_rate:.3f}, baseline={baseline_rate:.3f}, "
          f"lift={lift:.3f} ({lift*100:.1f}пп), "
          f"recovery_rate={len(recovered_ids)}/{len(problematic_ids)}={recovery_rate:.3f}, "
          f"h0_rejected={h0_rejected}")


if __name__ == "__main__":
    main()
