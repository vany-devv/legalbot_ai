"""H3 — нагрузочный прогон корпуса через /analyze/stream.

Каждый материал из corpus_h3.jsonl отправляется 3 раза последовательно
(concurrency=1). После каждого запроса из логов rag вытаскивается
analyze_total_ms и пишется в reports/runs.jsonl.

Структура runs.jsonl: {material_id, run_index, total_ms, request_id}.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).parent
CORPUS_PATH = ROOT / "corpus_h3.jsonl"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
OUT_PATH = REPORTS_DIR / "runs.jsonl"

ANALYZE_URL = "http://localhost:8000/analyze/stream"
RAG_CONTAINER = "legalbot_ai-rag-1"
RUNS_PER_MATERIAL = 3


def fetch_total_ms_after(since: str) -> tuple[int | None, str | None]:
    """Достаёт последнее analyze_total_ms из логов rag после момента since."""
    proc = subprocess.run(
        ["docker", "logs", RAG_CONTAINER, "--since", since],
        capture_output=True, text=True, timeout=30,
    )
    last_total: int | None = None
    last_request_id: str | None = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("msg") == "analyze_total_ms":
            last_total = obj.get("total_ms")
            last_request_id = obj.get("request_id")
    return last_total, last_request_id


def main() -> None:
    if not CORPUS_PATH.exists():
        sys.exit(f"Нет корпуса {CORPUS_PATH}. Запусти build_corpus.py.")

    materials = []
    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                materials.append(json.loads(line))
    print(f"Корпус H3: {len(materials)} материалов")

    records: list[dict] = []
    client = httpx.Client(timeout=120)

    overall_start = time.time()
    for mi, m in enumerate(materials, 1):
        for run_index in range(1, RUNS_PER_MATERIAL + 1):
            since = time.strftime("%Y-%m-%dT%H:%M:%S")
            t0 = time.time()
            try:
                r = client.post(
                    ANALYZE_URL, data={"text": m["text"]}, timeout=180,
                )
            except Exception as exc:
                print(f"   [{mi}/{len(materials)}] run {run_index}: ошибка {exc}")
                continue
            elapsed = time.time() - t0
            if r.status_code != 200:
                print(f"   [{mi}/{len(materials)}] run {run_index}: HTTP {r.status_code}")
                continue
            time.sleep(0.3)
            total_ms, request_id = fetch_total_ms_after(since)
            if total_ms is None:
                # fallback: используем замер от httpx
                total_ms = int(elapsed * 1000)
            records.append({
                "material_id": m["material_id"],
                "run_index": run_index,
                "total_ms": total_ms,
                "request_id": request_id,
            })
            print(f"   [{mi}/{len(materials)}] run {run_index}: {total_ms} ms")

    client.close()

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    elapsed = time.time() - overall_start
    print(f"\nИтого: {len(records)} замеров, общее время прогона {elapsed:.0f} сек")
    print(f"Сохранено в {OUT_PATH}")


if __name__ == "__main__":
    main()
