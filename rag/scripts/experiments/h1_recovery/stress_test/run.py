"""Стресс-прогон длинных рекламных материалов через /analyze/stream.

Каждый материал из stress_corpus.jsonl отправляется один раз. Цель -
получить от GigaChat реальные длинные json-ответы с несколькими рисками
и проверить, появляются ли в проде битые json при повышенной нагрузке.

Raw-выходы Stage 2 модель пишет в логи. Этот скрипт только инициирует
запросы, сбор raw делается отдельным extract_raws.py.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).parent
CORPUS_PATH = ROOT / "stress_corpus.jsonl"

ANALYZE_URL = "http://localhost:8000/analyze/stream"


def main() -> None:
    if not CORPUS_PATH.exists():
        sys.exit(f"Нет корпуса {CORPUS_PATH}.")

    materials = []
    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                materials.append(json.loads(line))
    print(f"Стресс-корпус: {len(materials)} материалов")

    client = httpx.Client(timeout=240)
    overall_start = time.time()

    ok = 0
    failed = 0
    for mi, m in enumerate(materials, 1):
        t0 = time.time()
        try:
            r = client.post(
                ANALYZE_URL, data={"text": m["text"]}, timeout=240,
            )
        except Exception as exc:
            print(f"   [{mi}/{len(materials)}] {m['material_id']}: ошибка {exc}")
            failed += 1
            continue
        elapsed = time.time() - t0
        if r.status_code != 200:
            print(f"   [{mi}/{len(materials)}] {m['material_id']}: HTTP {r.status_code}")
            failed += 1
            continue
        ok += 1
        print(f"   [{mi}/{len(materials)}] {m['material_id']} ({m['category']}, "
              f"{len(m['text'])} chars): {elapsed:.1f}s")

    client.close()
    total = time.time() - overall_start
    print(f"\nГотово: ok={ok}, failed={failed}, общее время {total:.0f} сек")


if __name__ == "__main__":
    main()
