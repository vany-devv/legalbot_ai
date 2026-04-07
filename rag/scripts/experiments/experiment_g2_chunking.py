#!/usr/bin/env python3
"""Эксперимент Г2 — Статья-ориентированный чанкинг НПА.

Проверяет гипотезу: статья-ориентированный парсер НПА обеспечивает
точность разметки статей ≥ 90% и целостность границ статей в чанках ≥ 95%
на корпусе из ≥ 5 НПА разных типов.

Использование:
    # Сгенерировать шаблон ground truth (автоматически прогоняет чанкер):
    python experiment_g2_chunking.py --generate-template --input-dir test_data/g3_documents

    # Запустить эксперимент:
    python experiment_g2_chunking.py --input-dir test_data/g3_documents --ground-truth test_data/ground_truth_g2.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.api.ingest import _extract_text  # noqa: E402
from app.core.chunking import ARTICLE_RE, LegalDocumentChunker, SimpleChunker  # noqa: E402

from report_utils import md_table, print_summary, save_json, save_markdown  # noqa: E402

LABELING_THRESHOLD = 0.90
BOUNDARY_THRESHOLD = 0.95


def generate_template(input_dir: Path, output_path: Path) -> None:
    """Extract text, run chunker, write a pre-filled template for manual review."""
    entries = []
    for f in sorted(input_dir.iterdir()):
        if f.suffix.lower() not in {".pdf", ".docx", ".rtf", ".txt"}:
            continue
        content = f.read_bytes()
        try:
            text = _extract_text(content, f.name)
        except Exception as exc:
            print(f"  ⚠️ {f.name}: ошибка извлечения — {exc}")
            continue

        # Run chunker to detect articles
        chunker = LegalDocumentChunker(law_name=f.stem)
        chunks = chunker.split(text)
        detected = sorted(set(
            c.meta.get("article", "")
            for c in chunks
            if c.meta.get("article") and c.meta["article"] != "preamble"
        ), key=lambda x: (len(x), x))

        entries.append({
            "filename": f.name,
            "doc_type": "kodeks",
            "law_name": f.stem,
            "expected_articles": detected,
            "total_expected_articles": len(detected),
            "notes": "проверь doc_type (kodeks/fz/postanovlenie/prikaz/reglament) и law_name",
        })
        print(f"  ✅ {f.name}: {len(chunks)} чанков, {len(detected)} статей")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nШаблон: {output_path}")
    print("Проверь doc_type, law_name и expected_articles для каждого файла.")


def check_boundary_integrity(chunk_content: str, chunk_article: str) -> bool:
    """Return True if chunk does NOT cross an article boundary.

    A chunk crosses a boundary if it contains article markers for 2+ distinct
    articles.  The chunker prepends the article header to continuation chunks,
    so we expect the *same* article number to appear — that is fine.
    """
    matches = ARTICLE_RE.findall(chunk_content)
    if not matches:
        return True  # no article markers at all — fine (preamble / punkt body)
    unique_articles = set(m[0] for m in matches)
    return len(unique_articles) <= 1


def check_labeling(chunk_content: str, chunk_article: str) -> bool:
    """Return True if the article label in metadata is consistent with content.

    - If meta says "preamble" — we accept if no article markers are inside.
    - Otherwise, any article marker found in the chunk must match meta.
    """
    if chunk_article == "preamble":
        matches = ARTICLE_RE.findall(chunk_content)
        return len(matches) == 0

    matches = ARTICLE_RE.findall(chunk_content)
    if not matches:
        # No explicit marker in body — can happen for continuation chunks
        # where header is the article line. Accept.
        return True
    # All found markers must match the meta article
    return all(m[0] == chunk_article for m in matches)


def run_experiment(input_dir: Path, ground_truth_path: Path, output_dir: Path) -> None:
    gt = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    print(f"Документов: {len(gt)}")
    print()

    doc_results = []

    total_chunks = 0
    total_labeling_ok = 0
    total_boundary_ok = 0

    for entry in gt:
        filename = entry["filename"]
        doc_type = entry.get("doc_type", "kodeks")
        law_name = entry.get("law_name", Path(filename).stem)
        expected_articles = set(entry.get("expected_articles", []))
        filepath = input_dir / filename

        doc_record = {
            "filename": filename,
            "doc_type": doc_type,
            "law_name": law_name,
            "expected_article_count": len(expected_articles),
        }

        if not filepath.exists():
            doc_record.update(error="файл не найден", chunks=0)
            doc_results.append(doc_record)
            print(f"  ❌ {filename} — не найден")
            continue

        # Extract text
        content = filepath.read_bytes()
        try:
            text = _extract_text(content, filename)
        except Exception as exc:
            doc_record.update(error=str(exc), chunks=0)
            doc_results.append(doc_record)
            print(f"  ❌ {filename} — ошибка извлечения: {exc}")
            continue

        # Chunk
        t0 = time.perf_counter()
        if doc_type in ("kodeks", "fz", "postanovlenie"):
            chunker = LegalDocumentChunker(law_name=law_name)
        else:
            chunker = SimpleChunker()
        chunks = chunker.split(text)
        elapsed = (time.perf_counter() - t0) * 1000

        # Analyze each chunk
        chunk_details = []
        labeling_ok = 0
        boundary_ok = 0

        for chunk in chunks:
            article = chunk.meta.get("article", "")
            lab_ok = check_labeling(chunk.content, article)
            bnd_ok = check_boundary_integrity(chunk.content, article)

            if lab_ok:
                labeling_ok += 1
            if bnd_ok:
                boundary_ok += 1

            chunk_details.append({
                "index": chunk.index,
                "article": article,
                "chars": len(chunk.content),
                "labeling_ok": lab_ok,
                "boundary_ok": bnd_ok,
            })

        n = len(chunks)
        total_chunks += n
        total_labeling_ok += labeling_ok
        total_boundary_ok += boundary_ok

        # Coverage
        detected_articles = set(
            c.meta.get("article", "")
            for c in chunks
            if c.meta.get("article") and c.meta["article"] != "preamble"
        )
        missing = sorted(expected_articles - detected_articles, key=lambda x: (len(x), x))
        extra = sorted(detected_articles - expected_articles, key=lambda x: (len(x), x))

        labeling_rate = labeling_ok / max(n, 1)
        boundary_rate = boundary_ok / max(n, 1)

        doc_record.update(
            chunks=n,
            labeling_ok=labeling_ok,
            labeling_rate=round(labeling_rate, 4),
            boundary_ok=boundary_ok,
            boundary_rate=round(boundary_rate, 4),
            detected_articles=len(detected_articles),
            missing_articles=missing[:10],
            extra_articles=extra[:10],
            time_ms=round(elapsed, 1),
        )
        doc_results.append(doc_record)

        lab_mark = "✅" if labeling_rate >= LABELING_THRESHOLD else "❌"
        bnd_mark = "✅" if boundary_rate >= BOUNDARY_THRESHOLD else "❌"
        print(f"  {filename} [{doc_type}]: {n} чанков, "
              f"разметка: {labeling_rate:.1%} {lab_mark}, "
              f"границы: {boundary_rate:.1%} {bnd_mark}, "
              f"статей: {len(detected_articles)}/{len(expected_articles)}, "
              f"{elapsed:.0f} мс")

    # Aggregates
    overall_labeling = total_labeling_ok / max(total_chunks, 1)
    overall_boundary = total_boundary_ok / max(total_chunks, 1)
    labeling_passed = overall_labeling >= LABELING_THRESHOLD
    boundary_passed = overall_boundary >= BOUNDARY_THRESHOLD

    summary = {
        "total_documents": len(doc_results),
        "total_chunks": total_chunks,
        "labeling_rate": round(overall_labeling, 4),
        "labeling_threshold": LABELING_THRESHOLD,
        "labeling_passed": labeling_passed,
        "boundary_rate": round(overall_boundary, 4),
        "boundary_threshold": BOUNDARY_THRESHOLD,
        "boundary_passed": boundary_passed,
        "hypothesis_confirmed": labeling_passed and boundary_passed,
    }

    full_results = {"summary": summary, "documents": doc_results}
    save_json(full_results, output_dir / "results_g2.json")

    # Markdown report
    summary_table = md_table(
        ["Метрика", "Значение", "Порог", "Результат"],
        [
            ["Точность разметки статей", f"{overall_labeling:.1%}", f"{LABELING_THRESHOLD:.0%}",
             "✅ PASS" if labeling_passed else "❌ FAIL"],
            ["Целостность границ статей", f"{overall_boundary:.1%}", f"{BOUNDARY_THRESHOLD:.0%}",
             "✅ PASS" if boundary_passed else "❌ FAIL"],
        ],
    )

    doc_table = md_table(
        ["Документ", "Тип", "Чанков", "Разметка", "Границы", "Статей (найд./ожид.)", "Время (мс)"],
        [
            [
                r["filename"],
                r.get("doc_type", "?"),
                r.get("chunks", 0),
                f"{r.get('labeling_rate', 0):.1%}" if r.get("chunks") else "—",
                f"{r.get('boundary_rate', 0):.1%}" if r.get("chunks") else "—",
                f"{r.get('detected_articles', 0)}/{r.get('expected_article_count', 0)}",
                f"{r.get('time_ms', 0):.0f}",
            ]
            for r in doc_results
        ],
    )

    # Boundary violations
    violations_text = ""
    for dr in doc_results:
        if dr.get("boundary_rate", 1) < 1.0 and dr.get("chunks", 0) > 0:
            violations_text += f"\n### {dr['filename']}\n"
            violations_text += f"Нарушений: {dr['chunks'] - dr['boundary_ok']} из {dr['chunks']} чанков\n"

    if not violations_text:
        violations_text = "Нарушений границ не обнаружено."

    # Coverage
    coverage_text = ""
    for dr in doc_results:
        missing = dr.get("missing_articles", [])
        extra = dr.get("extra_articles", [])
        if missing or extra:
            coverage_text += f"\n### {dr['filename']}\n"
            if missing:
                coverage_text += f"- Пропущенные статьи: {', '.join(missing[:20])}\n"
            if extra:
                coverage_text += f"- Лишние статьи: {', '.join(extra[:20])}\n"

    if not coverage_text:
        coverage_text = "Все ожидаемые статьи обнаружены."

    verdict = ("✅ **ГИПОТЕЗА Г2 ПОДТВЕРЖДЕНА**" if summary["hypothesis_confirmed"]
               else "❌ **ГИПОТЕЗА Г2 НЕ ПОДТВЕРЖДЕНА**")

    save_markdown(
        "Отчёт эксперимента Г2 — Чанкинг НПА",
        [
            ("Вердикт", verdict),
            ("Сводка метрик", summary_table),
            ("Детализация по документам", doc_table),
            ("Нарушения границ статей", violations_text),
            ("Покрытие статей", coverage_text),
            ("Параметры эксперимента",
             f"- Документов: {len(doc_results)}\n"
             f"- Всего чанков: {total_chunks}\n"
             f"- max_len: 1000, overlap: 150\n"
             f"- Порог точности разметки: {LABELING_THRESHOLD:.0%}\n"
             f"- Порог целостности границ: {BOUNDARY_THRESHOLD:.0%}"),
        ],
        output_dir / "report_g2.md",
    )

    print_summary({
        "Точность разметки статей": (overall_labeling, LABELING_THRESHOLD, labeling_passed),
        "Целостность границ статей": (overall_boundary, BOUNDARY_THRESHOLD, boundary_passed),
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="Эксперимент Г2 — Чанкинг НПА")
    parser.add_argument("--input-dir", type=Path, required=True, help="Папка с документами")
    parser.add_argument("--ground-truth", type=Path, help="JSON с ожидаемыми статьями")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "reports", help="Папка для отчётов")
    parser.add_argument("--generate-template", action="store_true", help="Сгенерировать шаблон ground truth")
    args = parser.parse_args()

    if args.generate_template:
        output = args.ground_truth or (args.input_dir.parent / "ground_truth_g2.json")
        generate_template(args.input_dir, output)
        return

    if not args.ground_truth:
        parser.error("Укажи --ground-truth или --generate-template")

    run_experiment(args.input_dir, args.ground_truth, args.output_dir)


if __name__ == "__main__":
    main()
