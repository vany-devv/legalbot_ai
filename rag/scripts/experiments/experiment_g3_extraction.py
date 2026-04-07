#!/usr/bin/env python3
"""Эксперимент Г3 — Извлечение текста из юридических документов.

Проверяет гипотезу: модуль извлечения текста (PDF/DOCX/RTF/MHTML)
обеспечивает долю успешно извлечённых документов ≥ 90%
и долю документов с сохранённой структурой ≥ 85%
на корпусе из ≥ 20 НПА с pravo.gov.ru.

Использование:
    # Сгенерировать шаблон ground truth:
    python experiment_g3_extraction.py --generate-template --input-dir test_data/g3_documents

    # Запустить эксперимент:
    python experiment_g3_extraction.py --input-dir test_data/g3_documents --ground-truth test_data/ground_truth_g3.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Allow imports from the rag package
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.api.ingest import _extract_text  # noqa: E402
from app.core.chunking import ARTICLE_RE  # noqa: E402

from report_utils import md_table, print_summary, save_json, save_markdown  # noqa: E402

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".rtf", ".txt"}

# Thresholds
EXTRACTION_THRESHOLD = 0.90
STRUCTURE_THRESHOLD = 0.85


def detect_format(filename: str, content: bytes) -> str:
    """Determine the real format of a file (especially RTF vs MHTML)."""
    name = filename.lower()
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith(".docx"):
        return "docx"
    if name.endswith(".rtf"):
        if content.lstrip()[:12].startswith(b"MIME-Version"):
            return "mhtml"
        return "rtf"
    return "other"


def generate_template(input_dir: Path, output_path: Path) -> None:
    """Scan *input_dir* and write a ground-truth template JSON."""
    entries = []
    for f in sorted(input_dir.iterdir()):
        if f.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        content = f.read_bytes()
        fmt = detect_format(f.name, content)
        # Try extraction to pre-fill article count
        try:
            text = _extract_text(content, f.name)
            articles = ARTICLE_RE.findall(text)
            article_count = len(set(a[0] for a in articles))
        except Exception:
            article_count = 0

        entries.append({
            "filename": f.name,
            "format": fmt,
            "expected_article_count": article_count,
            "expected_min_chars": len(text) if article_count else 0,
            "notes": "проверь и скорректируй expected_article_count",
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Шаблон сгенерирован: {output_path}")
    print(f"Файлов найдено: {len(entries)}")
    print("Проверь и скорректируй expected_article_count для каждого файла.")


def run_experiment(input_dir: Path, ground_truth_path: Path, output_dir: Path) -> None:
    """Run the G3 extraction experiment."""
    gt = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    print(f"Документов в ground truth: {len(gt)}")
    print(f"Папка с документами: {input_dir}")
    print()

    results = []

    for entry in gt:
        filename = entry["filename"]
        expected_articles = entry["expected_article_count"]
        expected_min_chars = entry.get("expected_min_chars", 0)
        filepath = input_dir / filename

        record = {
            "filename": filename,
            "format": entry.get("format", "unknown"),
            "expected_article_count": expected_articles,
        }

        if not filepath.exists():
            record.update(status="failure", error="файл не найден", chars=0, articles_found=0, time_ms=0)
            results.append(record)
            print(f"  ❌ {filename} — файл не найден")
            continue

        content = filepath.read_bytes()
        record["format"] = detect_format(filename, content)
        record["file_size_bytes"] = len(content)

        # Extract
        t0 = time.perf_counter()
        try:
            text = _extract_text(content, filename)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            record.update(status="failure", error=str(exc), chars=0, articles_found=0, time_ms=round(elapsed, 1))
            results.append(record)
            print(f"  ❌ {filename} — ошибка: {exc}")
            continue
        elapsed = (time.perf_counter() - t0) * 1000

        char_count = len(text)
        replacement_chars = text.count("\ufffd")
        replacement_ratio = replacement_chars / max(char_count, 1)

        # Find articles
        article_matches = ARTICLE_RE.findall(text)
        unique_articles = set(a[0] for a in article_matches)
        articles_found = len(unique_articles)

        # Determine extraction status
        is_empty = char_count < 100
        has_encoding_issues = replacement_ratio > 0.01
        chars_ok = expected_min_chars == 0 or char_count >= expected_min_chars * 0.9

        if is_empty:
            status = "failure"
            error = f"пустой вывод ({char_count} символов)"
        elif has_encoding_issues:
            status = "failure"
            error = f"проблемы кодировки ({replacement_ratio:.1%} замен)"
        elif not chars_ok:
            status = "partial"
            error = f"мало текста ({char_count} из ожидаемых {expected_min_chars})"
        else:
            status = "success"
            error = None

        # Structure preservation
        if expected_articles > 0:
            article_ratio = articles_found / expected_articles
            structure_preserved = 0.9 <= article_ratio <= 1.1
        else:
            structure_preserved = True  # no articles expected (e.g. postanovlenie)
            article_ratio = None

        record.update(
            status=status,
            error=error,
            chars=char_count,
            replacement_char_ratio=round(replacement_ratio, 4),
            articles_found=articles_found,
            article_ratio=round(article_ratio, 3) if article_ratio is not None else None,
            structure_preserved=structure_preserved,
            time_ms=round(elapsed, 1),
        )
        results.append(record)

        mark = "✅" if status == "success" else ("⚠️" if status == "partial" else "❌")
        struct_mark = "✅" if structure_preserved else "❌"
        print(f"  {mark} {filename} [{record['format']}] — {char_count} chars, "
              f"статей: {articles_found}/{expected_articles}, "
              f"структура: {struct_mark}, {elapsed:.0f} мс")

    # Aggregate metrics
    total = len(results)
    success_count = sum(1 for r in results if r["status"] in ("success", "partial"))
    extraction_rate = success_count / max(total, 1)

    structure_total = sum(1 for r in results if r["status"] != "failure")
    structure_ok = sum(1 for r in results if r.get("structure_preserved") and r["status"] != "failure")
    structure_rate = structure_ok / max(structure_total, 1)

    # Per-format breakdown
    formats = sorted(set(r["format"] for r in results))
    format_stats = {}
    for fmt in formats:
        fmt_results = [r for r in results if r["format"] == fmt]
        fmt_total = len(fmt_results)
        fmt_success = sum(1 for r in fmt_results if r["status"] in ("success", "partial"))
        fmt_structure = sum(1 for r in fmt_results if r.get("structure_preserved") and r["status"] != "failure")
        format_stats[fmt] = {
            "total": fmt_total,
            "success": fmt_success,
            "structure_ok": fmt_structure,
            "extraction_rate": round(fmt_success / max(fmt_total, 1), 3),
        }

    extraction_passed = extraction_rate >= EXTRACTION_THRESHOLD
    structure_passed = structure_rate >= STRUCTURE_THRESHOLD

    summary = {
        "total_documents": total,
        "extraction_rate": round(extraction_rate, 4),
        "extraction_threshold": EXTRACTION_THRESHOLD,
        "extraction_passed": extraction_passed,
        "structure_rate": round(structure_rate, 4),
        "structure_threshold": STRUCTURE_THRESHOLD,
        "structure_passed": structure_passed,
        "hypothesis_confirmed": extraction_passed and structure_passed,
        "format_breakdown": format_stats,
    }

    full_results = {"summary": summary, "details": results}

    # Save outputs
    save_json(full_results, output_dir / "results_g3.json")

    # Build markdown report
    summary_table = md_table(
        ["Метрика", "Значение", "Порог", "Результат"],
        [
            ["Доля успешно извлечённых", f"{extraction_rate:.1%}", f"{EXTRACTION_THRESHOLD:.0%}",
             "✅ PASS" if extraction_passed else "❌ FAIL"],
            ["Доля с сохранённой структурой", f"{structure_rate:.1%}", f"{STRUCTURE_THRESHOLD:.0%}",
             "✅ PASS" if structure_passed else "❌ FAIL"],
        ],
    )

    format_table = md_table(
        ["Формат", "Всего", "Успешно", "Структура ОК", "Доля извлечения"],
        [[fmt, s["total"], s["success"], s["structure_ok"], f"{s['extraction_rate']:.0%}"]
         for fmt, s in format_stats.items()],
    )

    detail_rows = []
    for r in results:
        status_mark = {"success": "✅", "partial": "⚠️", "failure": "❌"}.get(r["status"], "?")
        struct_mark = "✅" if r.get("structure_preserved") else "❌"
        detail_rows.append([
            r["filename"],
            r["format"],
            f"{r['chars']:,}",
            f"{r['articles_found']}/{r['expected_article_count']}",
            struct_mark,
            f"{r['time_ms']:.0f}",
            status_mark,
        ])

    detail_table = md_table(
        ["Файл", "Формат", "Символов", "Статей (найдено/ожид.)", "Структура", "Время (мс)", "Статус"],
        detail_rows,
    )

    errors_text = ""
    failures = [r for r in results if r["status"] == "failure"]
    if failures:
        errors_text = "\n".join(f"- **{r['filename']}**: {r.get('error', 'неизвестно')}" for r in failures)
    else:
        errors_text = "Ошибок не обнаружено."

    verdict = "✅ **ГИПОТЕЗА Г3 ПОДТВЕРЖДЕНА**" if summary["hypothesis_confirmed"] else "❌ **ГИПОТЕЗА Г3 НЕ ПОДТВЕРЖДЕНА**"

    save_markdown(
        "Отчёт эксперимента Г3 — Извлечение текста",
        [
            ("Вердикт", verdict),
            ("Сводка метрик", summary_table),
            ("Разбивка по форматам", format_table),
            ("Детализация по файлам", detail_table),
            ("Ошибки", errors_text),
            ("Параметры эксперимента",
             f"- Корпус: {total} документов\n"
             f"- Форматы: {', '.join(formats)}\n"
             f"- Порог успешного извлечения: {EXTRACTION_THRESHOLD:.0%}\n"
             f"- Порог сохранения структуры: {STRUCTURE_THRESHOLD:.0%}\n"
             f"- Допуск по количеству статей: ±10%"),
        ],
        output_dir / "report_g3.md",
    )

    print_summary({
        "Доля успешно извлечённых": (extraction_rate, EXTRACTION_THRESHOLD, extraction_passed),
        "Доля с сохранённой структурой": (structure_rate, STRUCTURE_THRESHOLD, structure_passed),
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="Эксперимент Г3 — Извлечение текста из НПА")
    parser.add_argument("--input-dir", type=Path, required=True, help="Папка с тестовыми документами")
    parser.add_argument("--ground-truth", type=Path, help="JSON с ожидаемыми данными по документам")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "reports", help="Папка для отчётов")
    parser.add_argument("--generate-template", action="store_true", help="Сгенерировать шаблон ground truth")
    args = parser.parse_args()

    if args.generate_template:
        output = args.ground_truth or (args.input_dir.parent / "ground_truth_g3.json")
        generate_template(args.input_dir, output)
        return

    if not args.ground_truth:
        parser.error("Укажи --ground-truth или --generate-template")

    run_experiment(args.input_dir, args.ground_truth, args.output_dir)


if __name__ == "__main__":
    main()
