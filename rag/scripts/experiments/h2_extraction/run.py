"""H2 — прогон модуля извлечения на корпусе.

Импортирует функции напрямую из app.api.analyze и app.api.ingest.
Для pdf вызывает _extract_pdf_paragraphs + _normalize_extracted_text,
для docx и txt — _extract_text + _normalize_extracted_text.
Сохраняет результаты в extracted/{material_id}.txt.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent
RAG_ROOT = ROOT.parent.parent.parent  # rag/
sys.path.insert(0, str(RAG_ROOT))

from app.api.analyze import _extract_pdf_paragraphs, _normalize_extracted_text  # noqa: E402
from app.api.ingest import _extract_text  # noqa: E402

CORPUS_DIR = ROOT / "corpus"
EXTRACTED_DIR = ROOT / "extracted"
EXTRACTED_DIR.mkdir(exist_ok=True)


def extract(file_path: Path) -> str:
    """Возвращает извлечённый и нормализованный текст материала."""
    content = file_path.read_bytes()
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        text = _extract_pdf_paragraphs(content)
    else:
        # _extract_text поддерживает docx, rtf и fallback на utf-8
        text = _extract_text(content, file_path.name)
    return _normalize_extracted_text(text)


def main() -> None:
    files = sorted(CORPUS_DIR.iterdir())
    files = [f for f in files if f.suffix.lower() in {".pdf", ".docx", ".txt"}]
    if not files:
        sys.exit("Нет файлов в corpus/. Запусти build_corpus.py.")

    for f in files:
        try:
            text = extract(f)
        except Exception as exc:
            text = ""
            print(f"[FAIL] {f.name}: {exc}")
        out = EXTRACTED_DIR / f"{f.stem}.txt"
        out.write_text(text, encoding="utf-8")
        print(f"[OK]   {f.name} -> {out.name}  ({len(text)} chars)")

    print(f"\nИзвлечено в {EXTRACTED_DIR}")


if __name__ == "__main__":
    main()
