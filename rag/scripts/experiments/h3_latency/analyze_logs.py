"""H3 — анализ результатов нагрузочного прогона.

Условия отвержения H₀ — три одновременно (pre-registered):
  1. p95 ≤ 60 000 мс. Индустриальный SLO для AI-pipeline на CPU LLM-инференсе
     (типовой диапазон 30–60 сек, см. Tene «How NOT to Measure Latency», 2013;
     обзоры Cloud Native APM benchmarks). Это жёстче, чем «продуктовый бюджет»
     5 минут / 90 сек — обеспечивает сопоставимость с внешней практикой.
  2. p99 ≤ 75 000 мс. Контроль хвоста распределения: длинные запросы
     не должны выходить за разумные границы.
  3. Доля точек с total_ms > 60 000 ≤ 5%. Дополнительная защита от
     ситуации «p95 проходит, но в выборке есть значимая доля выбросов».

Bootstrap-CI на p95 строится через scipy.stats.bootstrap (1000 ресемплов).
Дополнительное требование: верхняя граница CI на p95 также < 60 000 мс.

Сохраняет:
  - reports/report.json
  - reports/report.md
  - reports/chart_h3_latency_hist.png
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.stats import bootstrap  # type: ignore

ROOT = Path(__file__).parent
REPORTS_DIR = ROOT / "reports"
RUNS_PATH = REPORTS_DIR / "runs.jsonl"

THRESHOLD_P95_MS = 60_000
THRESHOLD_P99_MS = 75_000
THRESHOLD_OUTLIER_FRAC = 0.05  # доля точек > 60 000 мс


def load_runs() -> list[dict]:
    with RUNS_PATH.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def get_commit_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, cwd=ROOT,
        ).strip()
    except Exception:
        return "unknown"


def main() -> None:
    runs = load_runs()
    if not runs:
        raise SystemExit("Нет данных в runs.jsonl. Запусти run.py.")

    # Отбрасываем warm-up (run_index == 1)
    measured = [r for r in runs if r.get("run_index", 0) > 1]
    if len(measured) < 60:
        print(f"Внимание: после warm-up осталось {len(measured)} точек, "
              f"для надёжного p95 рекомендуется >= 100.")

    arr = np.array([r["total_ms"] for r in measured], dtype=float)
    p50 = float(np.percentile(arr, 50))
    p95 = float(np.percentile(arr, 95))
    p99 = float(np.percentile(arr, 99))

    # Bootstrap CI на p95
    rng = np.random.default_rng(42)
    res = bootstrap(
        (arr,),
        statistic=lambda a, axis=-1: np.percentile(a, 95, axis=axis),
        n_resamples=1000,
        confidence_level=0.95,
        method="basic",
        random_state=rng,
    )
    p95_low = float(res.confidence_interval.low)
    p95_high = float(res.confidence_interval.high)

    outlier_count = int((arr > THRESHOLD_P95_MS).sum())
    outlier_frac = outlier_count / len(arr)

    cond_p95 = (p95 <= THRESHOLD_P95_MS) and (p95_high < THRESHOLD_P95_MS)
    cond_p99 = p99 <= THRESHOLD_P99_MS
    cond_outlier = outlier_frac <= THRESHOLD_OUTLIER_FRAC
    h0_rejected = cond_p95 and cond_p99 and cond_outlier

    report = {
        "n_total": len(runs),
        "n_after_warmup": len(measured),
        "p50_ms": round(p50, 1),
        "p95_ms": round(p95, 1),
        "p99_ms": round(p99, 1),
        "p95_ci_low": round(p95_low, 1),
        "p95_ci_high": round(p95_high, 1),
        "outlier_count": outlier_count,
        "outlier_frac": round(outlier_frac, 4),
        "thresholds": {
            "p95_ms": THRESHOLD_P95_MS,
            "p99_ms": THRESHOLD_P99_MS,
            "outlier_frac": THRESHOLD_OUTLIER_FRAC,
        },
        "conditions": {
            "p95_le_threshold_with_ci": cond_p95,
            "p99_le_threshold": cond_p99,
            "outlier_frac_le_threshold": cond_outlier,
        },
        "h0_rejected": h0_rejected,
        "env_snapshot": {
            "commit_hash": get_commit_hash(),
            "python_version": os.popen("python3 --version").read().strip(),
            "model_provider": "GigaChat-Pro",
            "embedder_model": "Yandex-256",
            "corpus_size": len({r["material_id"] for r in measured}),
            "concurrency": 1,
            "finished_at": dt.datetime.now().isoformat(timespec="seconds"),
        },
    }
    (REPORTS_DIR / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    # Markdown
    md = [
        "# H3 — производительность пайплайна: результаты",
        "",
        f"Замеров после отбрасывания warm-up: **{len(measured)}** "
        f"(всего {len(runs)}, корпус из {len({r['material_id'] for r in measured})} материалов).",
        "",
        "## Перцентили (миллисекунды)",
        "",
        f"- p50: **{p50:.0f}**",
        f"- p95: **{p95:.0f}** (95% CI [{p95_low:.0f}, {p95_high:.0f}])",
        f"- p99: **{p99:.0f}**",
        f"- Точек выше 60 000 мс: {outlier_count} из {len(arr)} ({outlier_frac*100:.1f}%)",
        "",
        "## Условия отвержения H₀",
        "",
        f"1. p95 ≤ {THRESHOLD_P95_MS} мс и верхняя граница CI < {THRESHOLD_P95_MS}: "
        f"**{'выполнено' if cond_p95 else 'не выполнено'}**",
        f"2. p99 ≤ {THRESHOLD_P99_MS} мс: **{'выполнено' if cond_p99 else 'не выполнено'}**",
        f"3. Доля точек > {THRESHOLD_P95_MS} мс ≤ {THRESHOLD_OUTLIER_FRAC*100:.0f}%: "
        f"**{'выполнено' if cond_outlier else 'не выполнено'}**",
        "",
        f"H₀ отвергается: **{'ДА' if h0_rejected else 'НЕТ'}**",
        "",
        "## Обсуждение",
        "",
    ]
    if h0_rejected:
        md.append(
            "Все три условия выполнены. p95 укладывается в индустриальный SLO "
            "(60 секунд для AI-pipeline на CPU LLM-инференсе), хвост распределения "
            "(p99) тоже под контролем, доля выбросов — несущественная. "
            "Гипотеза H3 подтверждена."
        )
    else:
        md.append(
            "H₀ не отвергнута: одно или несколько условий не выполнены. Это значит, "
            "что в текущей конфигурации либо медианный хвост, либо распределение "
            "выбросов не укладываются в индустриальный SLO."
        )
    (REPORTS_DIR / "report.md").write_text("\n".join(md), encoding="utf-8")

    # Histogram
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(arr, bins=30, edgecolor="black", alpha=0.7)
    ax.axvline(THRESHOLD_P95_MS, color="red", linestyle="--",
               label=f"порог p95 = {THRESHOLD_P95_MS//1000} сек (индустриальный SLO)")
    ax.axvline(p95, color="green", linestyle="-", label=f"факт p95 = {p95:.0f} мс")
    ax.axvline(p99, color="orange", linestyle=":", label=f"факт p99 = {p99:.0f} мс")
    ax.set_xlabel("total_ms")
    ax.set_ylabel("Кол-во замеров")
    ax.set_title("H3: распределение времени отклика")
    ax.legend()
    fig.tight_layout()
    fig.savefig(REPORTS_DIR / "chart_h3_latency_hist.png", dpi=120)
    plt.close(fig)

    print(f"p50={p50:.0f}, p95={p95:.0f}, p99={p99:.0f}, "
          f"p95 CI=[{p95_low:.0f}, {p95_high:.0f}], "
          f"outliers={outlier_count}/{len(arr)} ({outlier_frac*100:.1f}%), "
          f"h0_rejected={h0_rejected}")


if __name__ == "__main__":
    main()
