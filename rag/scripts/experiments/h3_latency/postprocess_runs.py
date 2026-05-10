"""H3 — постобработка runs.jsonl: подмена httpx-замеров точными analyze_total_ms.

Из-за TZ-бага в run.py `fetch_total_ms_after` всегда возвращал None и
скрипт сохранял fallback-замер от httpx (полное время от send до получения
последнего byte). Этот скрипт читает логи rag за весь период прогона,
сопоставляет каждый замер с request_id и подменяет total_ms на точный
из логов.

Если request_id для записи отсутствует или не находится в логах,
запись остаётся с предыдущим значением.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
RUNS_PATH = ROOT / "reports" / "runs.jsonl"
RAG_CONTAINER = "legalbot_ai-rag-1"


def collect_total_ms_by_request() -> dict[str, int]:
    """Читает все analyze_total_ms из логов rag, индексирует по request_id."""
    proc = subprocess.run(
        ["docker", "logs", RAG_CONTAINER, "--since", "180m"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=60,
    )
    by_id: dict[str, int] = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("msg") == "analyze_total_ms":
            rid = obj.get("request_id")
            ms = obj.get("total_ms")
            if rid and ms is not None:
                by_id[rid] = ms
    return by_id


def main() -> None:
    by_id = collect_total_ms_by_request()
    print(f"Логов analyze_total_ms: {len(by_id)}")

    runs = []
    with RUNS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                runs.append(json.loads(line))
    print(f"Записей в runs.jsonl: {len(runs)}")

    replaced = 0
    diffs: list[int] = []
    for r in runs:
        rid = r.get("request_id")
        if rid and rid in by_id:
            old = r.get("total_ms")
            new = by_id[rid]
            if old is not None and old != new:
                diffs.append(abs(old - new))
            r["total_ms"] = new
            r["source_of_total_ms"] = "logs"
            replaced += 1
        else:
            r["source_of_total_ms"] = "httpx_fallback"

    print(f"Заменено total_ms из логов: {replaced} / {len(runs)}")
    if diffs:
        print(f"Расхождения httpx vs logs: avg={sum(diffs) / len(diffs):.0f}мс, "
              f"max={max(diffs)}мс")

    with RUNS_PATH.open("w", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Обновлено: {RUNS_PATH}")


if __name__ == "__main__":
    main()
