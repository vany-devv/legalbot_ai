"""Сборка корпуса H2 — pdf, docx и txt файлы из source_texts.MATERIALS.

Распределение по форматам — по 10 материалов на формат:
- pdf:  real_01..real_10
- docx: real_11..real_20
- txt:  real_21..real_30

Все 30 материалов имеют реальное текстовое содержание из открытых источников
(решения ФАС, продуктовые страницы УК, публикации Рекламного Совета).
Графическое оформление PDF/DOCX генерируется программно — это документировано
в methodology_v2.md как ограничение исследования.

Эталонная разметка expected_attributes/{material_id}.json создаётся одновременно
с каждым файлом — атрибуты объявлены в source_texts.MATERIALS.
"""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.lib.styles import ParagraphStyle
from docx import Document

from source_texts import MATERIALS

ROOT = Path(__file__).parent
CORPUS_DIR = ROOT / "corpus"
EXPECTED_DIR = ROOT / "expected_attributes"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)
EXPECTED_DIR.mkdir(parents=True, exist_ok=True)


# === Распределение по форматам ===
# Жёсткое распределение, не случайное — для воспроизводимости.
PDF_IDS = [f"real_{i:02d}" for i in range(1, 11)]    # real_01..real_10
DOCX_IDS = [f"real_{i:02d}" for i in range(11, 21)]  # real_11..real_20
TXT_IDS = [f"real_{i:02d}" for i in range(21, 31)]   # real_21..real_30


# === Регистрируем кириллический шрифт для reportlab ===
def _register_font():
    # На macOS обычно есть DejaVu или Helvetica с поддержкой кириллицы через Times.
    # Используем встроенный шрифт системы.
    candidates = [
        ("/System/Library/Fonts/Supplemental/Times New Roman.ttf", "TimesNewRoman"),
        ("/Library/Fonts/Arial.ttf", "Arial"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans"),
        ("/System/Library/Fonts/Helvetica.ttc", "Helvetica"),
    ]
    for path, name in candidates:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                addMapping(name, 0, 0, name)
                return name
            except Exception:
                continue
    return None  # fallback на дефолтный шрифт


FONT_NAME = _register_font()


def make_pdf(material_id: str, text: str, out_path: Path) -> None:
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50,
    )
    styles = getSampleStyleSheet()
    if FONT_NAME:
        body = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName=FONT_NAME,
            fontSize=11,
            leading=14,
        )
    else:
        body = styles["Normal"]
    story = []
    # Разбиваем текст на абзацы по точкам/предложениям для большей читаемости pdf
    parts = [p.strip() for p in text.split(". ") if p.strip()]
    for part in parts:
        if not part.endswith("."):
            part = part + "."
        story.append(Paragraph(part, body))
        story.append(Spacer(1, 8))
    doc.build(story)


def make_docx(material_id: str, text: str, out_path: Path) -> None:
    doc = Document()
    # Один материал = несколько абзацев
    parts = [p.strip() for p in text.split(". ") if p.strip()]
    for part in parts:
        if not part.endswith("."):
            part = part + "."
        doc.add_paragraph(part)
    doc.save(str(out_path))


def make_txt(material_id: str, text: str, out_path: Path) -> None:
    out_path.write_text(text, encoding="utf-8")


def write_expected(material: dict, out_path: Path) -> None:
    payload = {
        "material_id": material["material_id"],
        "format": material.get("_format"),
        "category": material["category"],
        "source_url": material.get("source_url"),
        "expected_attributes": material["expected_attributes"],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    materials_by_id = {m["material_id"]: m for m in MATERIALS}

    plan = (
        [(mid, "pdf") for mid in PDF_IDS]
        + [(mid, "docx") for mid in DOCX_IDS]
        + [(mid, "txt") for mid in TXT_IDS]
    )

    if len(plan) != len(MATERIALS):
        raise SystemExit(f"План покрывает {len(plan)} материалов, в MATERIALS {len(MATERIALS)}")

    for mid, fmt in plan:
        if mid not in materials_by_id:
            raise SystemExit(f"material_id {mid} не найден в MATERIALS")
        material = dict(materials_by_id[mid])
        material["_format"] = fmt
        out_name = f"{mid}.{fmt}"
        out_path = CORPUS_DIR / out_name
        if fmt == "pdf":
            make_pdf(mid, material["text"], out_path)
        elif fmt == "docx":
            make_docx(mid, material["text"], out_path)
        elif fmt == "txt":
            make_txt(mid, material["text"], out_path)
        else:
            raise SystemExit(f"Неизвестный формат: {fmt}")
        write_expected(material, EXPECTED_DIR / f"{mid}.json")
        print(f"[OK] {out_name}  ({material['category']})")

    print(f"\nИтого: {len(plan)} файлов сгенерировано в {CORPUS_DIR}")
    print(f"Эталонная разметка: {EXPECTED_DIR}")


if __name__ == "__main__":
    main()
