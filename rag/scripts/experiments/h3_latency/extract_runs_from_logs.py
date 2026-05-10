"""Сбор runs.jsonl из логов rag.

run.py зависал на одном из запросов и не дописал runs.jsonl, но в логах
rag-контейнера все analyze_total_ms события сохранены. Этот скрипт
читает их и формирует runs.jsonl.

Алгоритм:
1. Читает все analyze_total_ms из логов с момента старта прогона H3.
2. Берёт первые 150 событий (50 материалов × 3 итерации).
3. Сопоставляет с material_id из corpus_h3.jsonl: первый материал = 3 точки,
   второй = 3 и т.д. Это допустимое упрощение — для H3 (p95 latency)
   важно само распределение, а не привязка к конкретному материалу.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
RAG_CONTAINER = "legalbot_ai-rag-1"
CORPUS_PATH = ROOT / "corpus_h3.jsonl"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
OUT_PATH = REPORTS_DIR / "runs.jsonl"

# H3 стартовал примерно в 16:43 UTC (см. логи и task-notification).
# Берём с запасом: с 16:42 UTC.
START_UTC = "2026-05-09T16:42:00"


def collect_events() -> list[dict]:
    """Все analyze_total_ms из логов rag после START_UTC, в порядке времени."""
    proc = subprocess.run(
        ["docker", "logs", RAG_CONTAINER, "--since", START_UTC],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=60,
    )
    events: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("msg") == "analyze_total_ms":
            ts = obj.get("ts")
            ms = obj.get("total_ms")
            rid = obj.get("request_id")
            if ts and ms is not None:
                events.append({"ts": ts, "total_ms": ms, "request_id": rid})
    events.sort(key=lambda e: e["ts"])
    return events


def main() -> None:
    events = collect_events()
    print(f"analyze_total_ms событий с {START_UTC}: {len(events)}")

    # Загружаем материалы корпуса для привязки идентификаторов.
    materials = []
    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                materials.append(json.loads(line))
    print(f"Материалов в корпусе H3: {len(materials)}")

    runs_per_material = 3
    expected_points = len(materials) * runs_per_material
    if len(events) < expected_points:
        print(f"Событий меньше планового ({len(events)} < {expected_points}). "
              f"Берём что есть.")
    events = events[:expected_points]

    records: list[dict] = []
    for i, event in enumerate(events):
        material_index = i // runs_per_material
        run_index = (i % runs_per_material) + 1
        material_id = (
            materials[material_index]["material_id"]
            if material_index < len(materials)
            else f"unknown_{i}"
        )
        records.append({
            "material_id": material_id,
            "run_index": run_index,
            "total_ms": event["total_ms"],
            "request_id": event["request_id"],
            "source_of_total_ms": "logs",
        })

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    measured = [r for r in records if r["run_index"] > 1]
    if measured:
        ms = sorted(r["total_ms"] for r in measured)
        n = len(ms)
        p50 = ms[n // 2]
        p95 = ms[int(n * 0.95)]
        print(f"\nЗаписей всего: {len(records)} (warm-up: {len(records) - len(measured)})")
        print(f"После warm-up: {len(measured)} точек")
        print(f"Быстро прикинуть: p50≈{p50}, p95≈{p95}")
    print(f"Сохранено в {OUT_PATH}")


if __name__ == "__main__":
    main()
