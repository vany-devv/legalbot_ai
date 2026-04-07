#!/usr/bin/env python3
"""Пакетная загрузка документов в RAG-сервис.

Загружает все файлы из указанной папки через POST /ingest/upload
и ждёт завершения каждого job'а.

Использование:
    python ingest_all.py --input-dir test_data/g3_documents --api-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import time
import urllib.request
import urllib.parse
import json
import sys
from pathlib import Path

API_KEY = "dev-secret"

# Документы, которые пропускаем:
# - kodeks-117-fz: слишком большой (8901 чанков), timeout при Яндекс 1 RPS
# - уже загруженные из предыдущих запусков (upload удаляет старые чанки!)
SKIP_SOURCE_IDS = {
    "kodeks-117-fz",  # слишком большой (8901 чанков)
}

KODEKS_NUMBERS = {
    "74": "Водный кодекс РФ",
    "200": "Лесной кодекс РФ",
    "117": "Налоговый кодекс РФ (часть 2)",
    "1": "Уголовно-исполнительный кодекс РФ",
    "21": "Кодекс административного судопроизводства РФ",
    "138": "Гражданский процессуальный кодекс РФ",
    "174": "Уголовно-процессуальный кодекс РФ",
    "230": "Гражданский кодекс РФ (часть 4)",
    "146": "Налоговый кодекс РФ (часть 1)",
    "61": "Таможенный кодекс РФ",
    "188": "Жилищный кодекс РФ",
    "190": "Градостроительный кодекс РФ",
    "195": "Кодекс об административных правонарушениях РФ",
    "197": "Трудовой кодекс РФ",
    "145": "Бюджетный кодекс РФ",
    "146-1998": "Налоговый кодекс РФ (часть 1)",  # disambiguate
}


def get_law_name(filename: str) -> str:
    """Extract a human-readable law name from the filename."""
    if "Конституция" in filename:
        return "Конституция РФ"
    # Extract number from "№ NNN-ФЗ"
    import re
    m = re.search(r"№\s*(\d+)-ФЗ", filename)
    if m:
        num = m.group(1)
        if num in KODEKS_NUMBERS:
            return KODEKS_NUMBERS[num]
    # Fallback: use stem
    return Path(filename).stem[:80]


def get_source_id(filename: str) -> str:
    """Stable source_id from filename."""
    import re
    m = re.search(r"№\s*(\d+)-ФЗ", filename)
    if m:
        return f"kodeks-{m.group(1)}-fz"
    if "Конституция" in filename:
        return "konstitutsiya-rf"
    return Path(filename).stem[:50].lower().replace(" ", "-")


def upload_file(api_url: str, filepath: Path) -> str | None:
    """Upload a single file. Returns job_id or None on error."""
    source_id = get_source_id(filepath.name)
    law_name = get_law_name(filepath.name)

    # Build multipart form manually
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    content = filepath.read_bytes()

    body_parts = []
    # source_id
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"source_id\"\r\n\r\n{source_id}".encode())
    # title
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\n{law_name}".encode())
    # doc_type
    body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"doc_type\"\r\n\r\nkodeks".encode())
    # file
    filename_safe = filepath.name
    body_parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename_safe}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
        + content
    )
    body_parts.append(f"--{boundary}--".encode())

    body = b"\r\n".join(body_parts)

    req = urllib.request.Request(
        f"{api_url}/ingest/upload",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "X-Api-Key": API_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("job_id")
    except Exception as e:
        print(f"    ❌ Ошибка загрузки: {e}")
        return None


def wait_for_job(api_url: str, job_id: str, timeout: int = 7200) -> dict:
    """Poll job status until done or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(f"{api_url}/ingest/jobs/{job_id}", method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            status = data.get("status")
            progress = data.get("progress", 0)
            total = data.get("total", 0)
            if status == "done":
                return data
            if status == "failed":
                return data
            # Still running
            print(f"    ⏳ {status}: {progress}/{total} чанков...", end="\r")
            time.sleep(3)
        except Exception as e:
            print(f"\n    ⚠️  Ошибка опроса: {e}")
            time.sleep(3)
    return {"status": "timeout"}


def check_health(api_url: str) -> bool:
    try:
        req = urllib.request.Request(f"{api_url}/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return data.get("status") == "ok"
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Пакетная загрузка НПА в RAG-сервис")
    parser.add_argument("--input-dir", type=Path, required=True, help="Папка с документами")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000", help="URL RAG-сервиса")
    args = parser.parse_args()

    print(f"RAG-сервис: {args.api_url}")
    if not check_health(args.api_url):
        print("❌ RAG-сервис недоступен. Запусти его сначала.")
        sys.exit(1)
    print("✅ Сервис доступен\n")

    files = sorted(f for f in args.input_dir.iterdir()
                   if f.suffix.lower() in {".pdf", ".docx", ".rtf", ".txt"})
    print(f"Файлов для загрузки: {len(files)}\n")

    # Получить уже загруженные source_id
    already_loaded: set[str] = set()
    try:
        req = urllib.request.Request(f"{args.api_url}/ingest/documents", method="GET",
                                     headers={"X-Api-Key": API_KEY})
        with urllib.request.urlopen(req, timeout=10) as resp:
            docs = json.loads(resp.read())
            already_loaded = {d["source_id"] for d in docs}
            if already_loaded:
                print(f"Уже загружено в БД: {len(already_loaded)} документов (пропускаем)\n")
    except Exception:
        pass  # endpoint может не существовать — просто не пропускаем

    results = []
    for i, filepath in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {filepath.name[:70]}")
        source_id = get_source_id(filepath.name)
        print(f"    source_id: {source_id}")
        print(f"    title:     {get_law_name(filepath.name)}")

        if source_id in SKIP_SOURCE_IDS:
            print(f"    ⏭️  пропущен (в SKIP_SOURCE_IDS)\n")
            results.append({"file": filepath.name, "status": "skipped"})
            continue

        if source_id in already_loaded:
            print(f"    ⏭️  уже загружен, пропускаем\n")
            results.append({"file": filepath.name, "status": "skipped"})
            continue

        job_id = upload_file(args.api_url, filepath)
        if not job_id:
            results.append({"file": filepath.name, "status": "upload_failed"})
            continue

        print(f"    job_id: {job_id}")
        result = wait_for_job(args.api_url, job_id)
        status = result.get("status")
        chunks = result.get("chunks_added", 0)
        error = result.get("error")

        if status == "done":
            print(f"\r    ✅ done — {chunks} чанков добавлено           ")
        else:
            print(f"\r    ❌ {status}: {error}                           ")

        results.append({"file": filepath.name, "status": status, "chunks": chunks, "error": error})
        print()

    # Summary
    ok = sum(1 for r in results if r["status"] in ("done", "skipped"))
    print("=" * 60)
    print(f"Загружено: {ok}/{len(results)} документов")
    total_chunks = sum(r.get("chunks", 0) for r in results)
    print(f"Всего чанков: {total_chunks:,}")
    if total_chunks >= 5000:
        print("✅ Достаточно чанков для эксперимента Г1 (порог: 5 000)")
    else:
        print(f"⚠️  Чанков меньше 5 000 — Г1 можно запустить но это ниже порога")
    print("=" * 60)


if __name__ == "__main__":
    main()
