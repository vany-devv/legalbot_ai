"""Сборка корпуса H3 — подмножества корпуса H2 длиной до 10 000 символов.

Логика:
- Берёт все 30 файлов из ../h2_extraction/corpus/, извлекает текст
  (используя реальные функции пайплайна или просто читая txt).
- Если длина текста ≤ 10 000, добавляет в корпус.
- Если получилось < 50 материалов — добивает синтетическими короткими
  рекламными текстами (см. внутри файла).

Каждая запись в corpus_h3.jsonl: {material_id, text, length, source}.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
H2_CORPUS = ROOT.parent / "h2_extraction" / "corpus"
H2_EXPECTED = ROOT.parent / "h2_extraction" / "expected_attributes"
OUT_PATH = ROOT / "corpus_h3.jsonl"

# Чтобы не зависеть от extraction-функций сервиса, читаем тексты из
# source_texts (исходные тексты до помещения в pdf/docx).
sys.path.insert(0, str(ROOT.parent / "h2_extraction"))
from source_texts import MATERIALS  # noqa: E402

MAX_LENGTH = 10_000

# Дополнительные короткие рекламные тексты — для добивки до 50.
EXTRA_TEXTS = [
    {
        "material_id": "extra_01",
        "source": "synthetic",
        "text": "Откройте брокерский счёт в Финам! Без комиссий первый месяц. "
                "ООО «ИК Финам», лицензия № 077-08549-100000. finam.ru. Реклама.",
    },
    {
        "material_id": "extra_02",
        "source": "synthetic",
        "text": "Доставка пиццы за 30 минут или бесплатно. ДоДо Пицца. dodopizza.ru.",
    },
    {
        "material_id": "extra_03",
        "source": "synthetic",
        "text": "Курс «Английский с нуля» за 6 месяцев. Skyeng. "
                "Лицензия Минобрнауки № 040485 от 16.10.2018. skyeng.ru.",
    },
    {
        "material_id": "extra_04",
        "source": "synthetic",
        "text": "Каршеринг Делимобиль — поездки по городу от 7 рублей в минуту. "
                "ООО «Каршеринг Руссия». delimobil.ru.",
    },
    {
        "material_id": "extra_05",
        "source": "synthetic",
        "text": "Стоматологическая клиника «Дантист». Имплант под ключ — 49 000 рублей. "
                "Лицензия № ЛО-77-01-019742. dantist-msk.ru.",
    },
    {
        "material_id": "extra_06",
        "source": "synthetic",
        "text": "Premium-фитнес World Class. Безлимит без ограничений. Лицензия не требуется. "
                "worldclass.ru. Реклама.",
    },
    {
        "material_id": "extra_07",
        "source": "synthetic",
        "text": "Туры в Турцию, всё включено, от 35 000 рублей. ООО «Тез Тур». "
                "tez-tour.com. Реклама.",
    },
    {
        "material_id": "extra_08",
        "source": "synthetic",
        "text": "Доставка готовой еды Grow Food. Меню на неделю — от 4 990 рублей. "
                "growfood.pro. Реклама.",
    },
    {
        "material_id": "extra_09",
        "source": "synthetic",
        "text": "Школа программирования для детей «Алгоритмика». "
                "ООО «Алгоритмика», лицензия Минобрнауки № 040055. algoritmika.org.",
    },
    {
        "material_id": "extra_10",
        "source": "synthetic",
        "text": "Юридическое сопровождение бизнеса. Гарант-Право. "
                "garant-pravo.ru. Реклама.",
    },
    {
        "material_id": "extra_11",
        "source": "synthetic",
        "text": "Авиабилеты Москва-Сочи от 3 990 рублей. Победа. pobeda.aero. Реклама.",
    },
    {
        "material_id": "extra_12",
        "source": "synthetic",
        "text": "Доставка цветов 24/7. Букет от 1 990 рублей. flower-msk.ru. Реклама.",
    },
    {
        "material_id": "extra_13",
        "source": "synthetic",
        "text": "Мебель ИКЕА — стиль, функциональность, доступная цена. ikea.ru. Реклама.",
    },
    {
        "material_id": "extra_14",
        "source": "synthetic",
        "text": "Аренда серверов от REG.RU. От 99 рублей в месяц. reg.ru. Реклама.",
    },
    {
        "material_id": "extra_15",
        "source": "synthetic",
        "text": "Доставка из любых ресторанов Москвы. Яндекс Еда. eda.yandex. Реклама.",
    },
    {
        "material_id": "extra_16",
        "source": "synthetic",
        "text": "Вакансии в IT — найди работу мечты на HeadHunter. hh.ru. Реклама.",
    },
    {
        "material_id": "extra_17",
        "source": "synthetic",
        "text": "Психотерапия онлайн от 2 500 рублей. Платформа Ясно. "
                "ООО «Ясно Технологии». yasno.live. Реклама.",
    },
    {
        "material_id": "extra_18",
        "source": "synthetic",
        "text": "Фотостудии Москвы — выбирай и бронируй на Photostudios. photostudios.ru.",
    },
    {
        "material_id": "extra_19",
        "source": "synthetic",
        "text": "Курсы вождения «Автостоп». Лицензия № ЛО-77-04-002142. "
                "Стоимость от 28 000 рублей. avtostop-msk.ru. Реклама.",
    },
    {
        "material_id": "extra_20",
        "source": "synthetic",
        "text": "Свадебная фотосъёмка от 25 000 рублей. studio-svadba.ru. Реклама.",
    },
]


def main() -> None:
    records: list[dict] = []
    seen_ids: set[str] = set()

    # 1) Все материалы из H2
    for m in MATERIALS:
        text = m["text"]
        if len(text) <= MAX_LENGTH:
            records.append({
                "material_id": m["material_id"],
                "text": text,
                "length": len(text),
                "source": m["source"],
            })
            seen_ids.add(m["material_id"])

    # 2) Добивка до 50
    for extra in EXTRA_TEXTS:
        if len(records) >= 50:
            break
        if extra["material_id"] in seen_ids:
            continue
        text = extra["text"]
        if len(text) > MAX_LENGTH:
            continue
        records.append({
            "material_id": extra["material_id"],
            "text": text,
            "length": len(text),
            "source": extra["source"],
        })

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    real_count = sum(1 for r in records if r["source"] == "real")
    synth_count = sum(1 for r in records if r["source"] == "synthetic")
    print(f"Всего: {len(records)} материалов")
    print(f"Real:   {real_count}")
    print(f"Synth:  {synth_count}")
    print(f"Длина: min={min(r['length'] for r in records)}, "
          f"max={max(r['length'] for r in records)}, "
          f"avg={sum(r['length'] for r in records) / len(records):.0f}")
    print(f"Сохранено в {OUT_PATH}")


if __name__ == "__main__":
    main()
