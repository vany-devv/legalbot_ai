"""H2 — сопоставление извлечённого текста с эталоном и расчёт метрик.

Метрики:
  - success_rate: материал считается успешным, если
      длина >= 100, доля unicode-replacement < 1%, мусорных control < 5.
  - preservation_rate: средний attr_score по материалам, где
      attr_score = |attrs_found| / |attrs_expected|.
  - per-format breakdown.

Эталон: expected_attributes/{material_id}.json (с полем expected_attributes).

Алгоритм совпадения атрибута:
- substring match с нормализацией (lowercase, удаление лишних пробелов,
  замена кавычек/тире на стандартные).
- для номеров (license_number, phone) — сравнение только цифр.

Сохраняет:
  - reports/per_material.csv
  - reports/report.json
  - reports/report.md
  - reports/chart_h2_success_by_format.png
  - reports/chart_h2_attribute_heatmap.png
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import subprocess
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).parent
CORPUS_DIR = ROOT / "corpus"
EXPECTED_DIR = ROOT / "expected_attributes"
EXTRACTED_DIR = ROOT / "extracted"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

THRESHOLD_SUCCESS = 0.90
THRESHOLD_PRESERVATION = 0.85

REPLACEMENT_CHAR = "�"
NUMERIC_FIELDS = {"license_number", "phone"}


def normalize_text(s: str) -> str:
    s = s.lower()
    # унификация кавычек и тире
    s = s.replace("«", "\"").replace("»", "\"").replace("„", "\"").replace("“", "\"").replace("”", "\"")
    s = s.replace("–", "-").replace("—", "-")
    # схлопываем пробелы
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def is_success(text: str) -> bool:
    if len(text) < 100:
        return False
    repl = text.count(REPLACEMENT_CHAR)
    if len(text) > 0 and repl / len(text) >= 0.01:
        return False
    # control characters (без \n, \r, \t)
    control = sum(1 for ch in text if ord(ch) < 32 and ch not in "\n\r\t")
    if control >= 5:
        return False
    return True


def attribute_found(value, extracted: str) -> bool:
    if value is None or value == "" or value == "null":
        return False
    if isinstance(value, (int, float)):
        value = str(value)
    return normalize_text(str(value)) in normalize_text(extracted)


def attribute_found_numeric(value, extracted: str) -> bool:
    if value is None or value == "":
        return False
    digits_value = normalize_digits(str(value))
    if not digits_value:
        return False
    digits_extracted = normalize_digits(extracted)
    return digits_value in digits_extracted


def score_material(material_id: str, fmt: str) -> dict:
    extracted_path = EXTRACTED_DIR / f"{material_id}.txt"
    expected_path = EXPECTED_DIR / f"{material_id}.json"
    if not extracted_path.exists() or not expected_path.exists():
        return {
            "material_id": material_id, "format": fmt, "success": False,
            "attr_found": 0, "attr_total": 0, "attr_score": 0.0,
            "error_reason": "missing_files",
        }
    extracted = extracted_path.read_text(encoding="utf-8")
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    expected_attrs = expected.get("expected_attributes", {})
    # отбрасываем null/пустые
    expected_attrs = {k: v for k, v in expected_attrs.items() if v not in (None, "", "null")}

    success = is_success(extracted)

    found = 0
    total = len(expected_attrs)
    missing_attrs: list[str] = []
    for key, value in expected_attrs.items():
        if key in NUMERIC_FIELDS:
            ok = attribute_found_numeric(value, extracted)
        else:
            ok = attribute_found(value, extracted)
        if ok:
            found += 1
        else:
            missing_attrs.append(key)

    attr_score = (found / total) if total > 0 else 1.0

    error_reason = ""
    if not success:
        if len(extracted) < 100:
            error_reason = "empty_or_short"
        else:
            error_reason = "broken_encoding_or_control"
    elif attr_score < 1.0:
        error_reason = f"missing_attrs:{','.join(missing_attrs)}"

    return {
        "material_id": material_id,
        "format": fmt,
        "success": success,
        "attr_found": found,
        "attr_total": total,
        "attr_score": round(attr_score, 4),
        "error_reason": error_reason,
    }


def get_commit_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, cwd=ROOT,
        ).strip()
    except Exception:
        return "unknown"


def main() -> None:
    files = sorted(CORPUS_DIR.iterdir())
    files = [f for f in files if f.suffix.lower() in {".pdf", ".docx", ".txt"}]
    if not files:
        raise SystemExit("Нет файлов в corpus/. Запусти build_corpus.py + run.py.")

    rows: list[dict] = []
    for f in files:
        rows.append(score_material(f.stem, f.suffix.lower().lstrip(".")))

    # CSV
    csv_path = REPORTS_DIR / "per_material.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Метрики
    n = len(rows)
    success_count = sum(1 for r in rows if r["success"])
    success_rate = success_count / n
    preservation_rate = sum(r["attr_score"] for r in rows) / n

    # Per-format
    per_format = {}
    for fmt in ("pdf", "docx", "txt"):
        sub = [r for r in rows if r["format"] == fmt]
        if not sub:
            continue
        per_format[fmt] = {
            "n": len(sub),
            "success_rate": round(sum(1 for r in sub if r["success"]) / len(sub), 4),
            "preservation_rate": round(sum(r["attr_score"] for r in sub) / len(sub), 4),
        }

    h0_rejected = (success_rate >= THRESHOLD_SUCCESS) and (preservation_rate >= THRESHOLD_PRESERVATION)

    report = {
        "n": n,
        "success_rate": round(success_rate, 4),
        "preservation_rate": round(preservation_rate, 4),
        "threshold_success": THRESHOLD_SUCCESS,
        "threshold_preservation": THRESHOLD_PRESERVATION,
        "h0_rejected": h0_rejected,
        "per_format": per_format,
        "env_snapshot": {
            "commit_hash": get_commit_hash(),
            "python_version": os.popen("python3 --version").read().strip(),
            "corpus_size": n,
            "finished_at": dt.datetime.now().isoformat(timespec="seconds"),
        },
    }
    (REPORTS_DIR / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    # Markdown
    md = [
        "# H2 — извлечение текста: результаты",
        "",
        f"Корпус: {n} материалов (pdf+docx+txt).",
        "",
        "## Сводные метрики",
        "",
        f"- success_rate: **{success_rate:.3f}** (порог ≥ {THRESHOLD_SUCCESS})",
        f"- preservation_rate: **{preservation_rate:.3f}** (порог ≥ {THRESHOLD_PRESERVATION})",
        f"- H₀ отвергается: **{'ДА' if h0_rejected else 'НЕТ'}**",
        "",
        "## Per-format",
        "",
        "| Формат | n | success_rate | preservation_rate |",
        "|---|---|---|---|",
    ]
    for fmt, vals in per_format.items():
        md.append(f"| {fmt} | {vals['n']} | {vals['success_rate']} | {vals['preservation_rate']} |")
    md.append("")
    md.append("## Материалы с проблемами")
    md.append("")
    md.append("| material_id | format | attr_score | error_reason |")
    md.append("|---|---|---|---|")
    for r in rows:
        if not r["success"] or r["attr_score"] < 1.0:
            md.append(f"| {r['material_id']} | {r['format']} | {r['attr_score']} | {r['error_reason']} |")
    (REPORTS_DIR / "report.md").write_text("\n".join(md), encoding="utf-8")

    # Chart 1: success by format
    formats = list(per_format.keys())
    sr = [per_format[f]["success_rate"] for f in formats]
    pr = [per_format[f]["preservation_rate"] for f in formats]
    fig, ax = plt.subplots(figsize=(7, 5))
    x = range(len(formats))
    width = 0.35
    ax.bar([i - width / 2 for i in x], sr, width, label="success_rate")
    ax.bar([i + width / 2 for i in x], pr, width, label="preservation_rate")
    ax.axhline(THRESHOLD_SUCCESS, color="gray", linestyle="--", linewidth=0.7)
    ax.axhline(THRESHOLD_PRESERVATION, color="black", linestyle="--", linewidth=0.7)
    ax.set_xticks(list(x))
    ax.set_xticklabels(formats)
    ax.set_ylim(0, 1.05)
    ax.set_title("H2: метрики по форматам")
    ax.legend()
    fig.tight_layout()
    fig.savefig(REPORTS_DIR / "chart_h2_success_by_format.png", dpi=120)
    plt.close(fig)

    # Chart 2: attribute heatmap (формат vs атрибут)
    all_attrs: set[str] = set()
    for f in files:
        ep = EXPECTED_DIR / f"{f.stem}.json"
        if ep.exists():
            data = json.loads(ep.read_text(encoding="utf-8"))
            all_attrs.update(
                k for k, v in data.get("expected_attributes", {}).items()
                if v not in (None, "", "null")
            )
    all_attrs_list = sorted(all_attrs)
    grid = []
    for fmt in formats:
        row = []
        for attr in all_attrs_list:
            present = 0
            found = 0
            for f in files:
                if f.suffix.lower().lstrip(".") != fmt:
                    continue
                ep = EXPECTED_DIR / f"{f.stem}.json"
                if not ep.exists():
                    continue
                data = json.loads(ep.read_text(encoding="utf-8"))
                expected = data.get("expected_attributes", {})
                value = expected.get(attr)
                if value in (None, "", "null"):
                    continue
                present += 1
                extracted = (EXTRACTED_DIR / f"{f.stem}.txt").read_text(encoding="utf-8")
                if attr in NUMERIC_FIELDS:
                    if attribute_found_numeric(value, extracted):
                        found += 1
                else:
                    if attribute_found(value, extracted):
                        found += 1
            ratio = (found / present) if present else float("nan")
            row.append(ratio)
        grid.append(row)

    if grid:
        fig, ax = plt.subplots(figsize=(max(8, len(all_attrs_list) * 0.6), 4))
        im = ax.imshow(grid, vmin=0, vmax=1, aspect="auto", cmap="RdYlGn")
        ax.set_xticks(range(len(all_attrs_list)))
        ax.set_xticklabels(all_attrs_list, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(formats)))
        ax.set_yticklabels(formats)
        ax.set_title("H2: доля сохранённых атрибутов (формат × атрибут)")
        for i, row in enumerate(grid):
            for j, val in enumerate(row):
                if val == val:  # not nan
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im, ax=ax, fraction=0.02)
        fig.tight_layout()
        fig.savefig(REPORTS_DIR / "chart_h2_attribute_heatmap.png", dpi=120)
        plt.close(fig)

    print(f"success_rate={success_rate:.3f}, preservation_rate={preservation_rate:.3f}, "
          f"h0_rejected={h0_rejected}")
    print(f"Отчёты в {REPORTS_DIR}")


if __name__ == "__main__":
    main()
