"""Извлечение raw-выходов GigaChat из логов rag для стресс-теста.

Берет последние 20 событий [ANALYZE] LLM raw output из логов (по числу
материалов в стресс-корпусе) и сохраняет в stress_raws.jsonl. Затем
считает долю проблемных raw - тех, на которых стандартный json.loads
падает без всякой подготовки.

Цель эксперимента: проверить, ломает ли реальный GigaChat-Pro json
на длинных сложных материалах. На исходном корпусе H1 (короткие
тексты) этот процент был 0%, что и поставило под сомнение полезность
recovery-механизма.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
RAG_CONTAINER = "legalbot_ai-rag-1"
CORPUS_PATH = ROOT / "stress_corpus.jsonl"
OUT_PATH = ROOT / "stress_raws.jsonl"


def is_problematic(raw: str) -> bool:
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


def extract_raws() -> list[dict]:
    proc = subprocess.run(
        ["docker", "logs", RAG_CONTAINER, "--since", "30m"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=60,
    )
    raws: list[dict] = []
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
            raw = msg.split("[ANALYZE] LLM raw output:", 1)[1].lstrip("\n")
            raws.append({
                "request_id": obj.get("request_id"),
                "ts": obj.get("ts"),
                "raw": raw,
            })
    raws.sort(key=lambda r: r["ts"] or "")
    return raws


def main() -> None:
    materials = []
    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                materials.append(json.loads(line))

    raws = extract_raws()
    print(f"Извлечено raw из логов (за 30 мин): {len(raws)}")

    # Берём последние N raw, где N = размер корпуса.
    n = len(materials)
    last_raws = raws[-n:] if len(raws) >= n else raws
    print(f"Берём последние {len(last_raws)} raw для стресс-теста")

    records: list[dict] = []
    for i, r in enumerate(last_raws):
        m = materials[i] if i < len(materials) else {"material_id": f"unknown_{i}", "category": "?"}
        prob = is_problematic(r["raw"])
        records.append({
            "material_id": m["material_id"],
            "category": m.get("category"),
            "text_length": len(m.get("text", "")),
            "raw": r["raw"],
            "raw_length": len(r["raw"]),
            "problematic": prob,
            "request_id": r.get("request_id"),
        })

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total = len(records)
    prob_count = sum(1 for r in records if r["problematic"])
    print(f"\n=== Стресс-тест raw ===")
    print(f"Всего: {total}")
    print(f"Проблемных (json.loads падает): {prob_count} ({prob_count/total*100:.1f}%)")
    if prob_count:
        print("\nПроблемные материалы:")
        for r in records:
            if r["problematic"]:
                print(f"  - {r['material_id']} ({r['category']}, "
                      f"text={r['text_length']} chars, raw={r['raw_length']} chars)")
    print(f"\nСохранено в {OUT_PATH}")


if __name__ == "__main__":
    main()
