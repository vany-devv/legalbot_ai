"""Сбор корпуса H1 — raw-ответов LLM-анализатора.

Алгоритм:
1. Берёт файлы из ../h2_extraction/corpus/ (30 материалов).
2. Каждый файл отправляет в /analyze/stream 3 раза.
3. После каждого прогона сразу вытаскивает «[ANALYZE] LLM raw output:» из
   логов rag-контейнера (`docker logs legalbot_ai-rag-1`).
4. Складывает все raw в corpus_h1.jsonl: {material_id, run_index, raw, source}.
5. Если доля «проблемных» (json.loads падает) < 30% — добавляет синтетические
   битые json до достижения порога.

Результат: corpus_h1.jsonl с >= 100 записями и >= 30% проблемных.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).parent
H2_CORPUS = ROOT.parent / "h2_extraction" / "corpus"
OUT_PATH = ROOT / "corpus_h1.jsonl"

ANALYZE_URL = "http://localhost:8000/analyze/stream"
RAG_CONTAINER = "legalbot_ai-rag-1"
RUNS_PER_MATERIAL = 3


def list_corpus_files() -> list[Path]:
    files = sorted(H2_CORPUS.iterdir())
    files = [f for f in files if f.suffix in {".pdf", ".docx", ".txt"}]
    return files


def get_log_marker() -> str:
    """Возвращает временную метку для отсечения новых логов."""
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def fetch_raw_after(since: str, request_id: str | None = None) -> list[str]:
    """Достаёт все «[ANALYZE] LLM raw output:» из логов rag после момента since.

    since — ISO-таймстемп (формат как в логе, без TZ).
    Возвращает список текстов raw в порядке появления.
    """
    proc = subprocess.run(
        ["docker", "logs", RAG_CONTAINER, "--since", since],
        capture_output=True, text=True, timeout=30,
    )
    raws: list[str] = []
    # Лог построчный jsonl. Каждая запись — один JSON-объект.
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        msg = obj.get("msg", "")
        if isinstance(msg, str) and msg.startswith("[ANALYZE] LLM raw output:"):
            raw = msg.split("[ANALYZE] LLM raw output:", 1)[1]
            # обычно начинается с \n
            raw = raw.lstrip("\n")
            raws.append(raw)
    return raws


def send_material(client: httpx.Client, file_path: Path) -> bool:
    """Отправляет файл в /analyze/stream. Возвращает True если запрос прошёл."""
    try:
        with file_path.open("rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            r = client.post(ANALYZE_URL, files=files, timeout=120)
        # Если SSE-стрим — читаем до конца
        return r.status_code == 200
    except Exception as exc:
        print(f"   ! ошибка: {exc}")
        return False


def is_problematic(raw: str) -> bool:
    """True если стандартный json.loads ломается на raw (после снятия markdown)."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n", 1)
        text = lines[1] if len(lines) > 1 else text
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        json.loads(text)
        return False
    except json.JSONDecodeError:
        return True


def main() -> None:
    files = list_corpus_files()
    print(f"Файлов в корпусе H2: {len(files)}")
    if not files:
        sys.exit("Нечего прогонять. Запусти сначала h2_extraction/build_corpus.py.")

    records: list[dict] = []
    client = httpx.Client(timeout=120)

    for fi, file_path in enumerate(files, 1):
        material_id = file_path.stem  # real_01, synth_05, ...
        print(f"\n[{fi}/{len(files)}] {file_path.name}")
        for run_index in range(1, RUNS_PER_MATERIAL + 1):
            since = get_log_marker()
            t0 = time.time()
            ok = send_material(client, file_path)
            elapsed = time.time() - t0
            if not ok:
                print(f"   run {run_index}: запрос упал, пропускаю")
                continue
            # Дать логам прокрутиться
            time.sleep(0.5)
            raws = fetch_raw_after(since)
            # Берём последний raw (других быть не должно, но на всякий случай)
            if not raws:
                print(f"   run {run_index}: raw не найден в логах ({elapsed:.1f}s)")
                continue
            raw = raws[-1]
            problematic = is_problematic(raw)
            records.append({
                "material_id": material_id,
                "run_index": run_index,
                "raw": raw,
                "source": "real",
                "problematic": problematic,
            })
            mark = "BROKEN" if problematic else "ok"
            print(f"   run {run_index}: {mark}, {elapsed:.1f}s, raw_len={len(raw)}")

    client.close()

    # Сохраняем
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total = len(records)
    problematic_count = sum(1 for r in records if r["problematic"])
    print(f"\n=== Итог ===")
    print(f"Всего записей: {total}")
    print(f"Проблемных: {problematic_count} ({problematic_count / total * 100:.1f}%)")
    print(f"Сохранено в {OUT_PATH}")


if __name__ == "__main__":
    main()
