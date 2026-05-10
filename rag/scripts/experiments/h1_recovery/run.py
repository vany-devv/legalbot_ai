"""H1 — offline replay парсера на корпусе corpus_h1.jsonl.

Делает два прогона:
  - run A: settings.analyze_recovery_enabled = True (полный пайплайн парсинга)
  - run B: settings.analyze_recovery_enabled = False (только json.loads)

Для каждой записи корпуса вызывает _parse_json напрямую (без HTTP) и
фиксирует parse_path. Результаты в reports/runA.jsonl и reports/runB.jsonl.

Перед каждой прогонкой важно подменить значение settings.analyze_recovery_enabled
до импорта analyze (чтобы _parse_json увидел нужный флаг).
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).parent
RAG_ROOT = ROOT.parent.parent.parent  # rag/
sys.path.insert(0, str(RAG_ROOT))

CORPUS_PATH = ROOT / "corpus_h1.jsonl"
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


# === Перехват логов parse_event ===
class ParseEventCollector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.events: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        if record.getMessage() == "parse_event":
            parse_path = getattr(record, "parse_path", None)
            if parse_path:
                self.events.append(parse_path)


def run_replay(corpus: list[dict], recovery_enabled: bool, label: str) -> list[dict]:
    """Прогон корпуса с заданным значением флага."""
    # Подменяем флаг до импорта analyze
    from app.config import settings
    settings.analyze_recovery_enabled = recovery_enabled

    # (Пере)импорт _parse_json — берёт settings из памяти, в которой мы изменили флаг.
    if "app.api.analyze" in sys.modules:
        del sys.modules["app.api.analyze"]
    from app.api.analyze import _parse_json  # noqa: E402

    # Перехватываем parse_event-логи именно из этого модуля.
    collector = ParseEventCollector()
    analyze_logger = logging.getLogger("app.api.analyze")
    analyze_logger.addHandler(collector)
    analyze_logger.setLevel(logging.INFO)

    results: list[dict] = []
    for rec in corpus:
        collector.events.clear()
        # Глушим warning-логи парсера (они только мешают читать stdout)
        with io.StringIO() as buf, redirect_stdout(buf):
            try:
                _parse_json(rec["raw"])
            except Exception as exc:
                # _parse_json ловит исключения сам, но на всякий случай
                pass
        # Берём последний parse_path (на один вызов — одно событие)
        parse_path = collector.events[-1] if collector.events else "unknown"
        raw_hash = hashlib.sha256(rec["raw"].encode("utf-8")).hexdigest()[:16]
        results.append({
            "material_id": rec["material_id"],
            "run_index": rec.get("run_index"),
            "raw_hash": raw_hash,
            "parse_path": parse_path,
            "source": rec.get("source"),
            "problematic_oracle": rec.get("problematic"),
        })

    analyze_logger.removeHandler(collector)
    print(f"{label}: {len(results)} записей; распределение parse_path:")
    distribution: dict[str, int] = {}
    for r in results:
        distribution[r["parse_path"]] = distribution.get(r["parse_path"], 0) + 1
    for path, n in sorted(distribution.items(), key=lambda x: -x[1]):
        print(f"  {path:24s} {n}")
    return results


def main() -> None:
    if not CORPUS_PATH.exists():
        sys.exit(f"Нет корпуса {CORPUS_PATH}. Запусти collect_corpus.py.")

    corpus = []
    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            corpus.append(json.loads(line))
    print(f"Загружен корпус: {len(corpus)} записей")

    print("\n=== run A (recovery=True) ===")
    run_a = run_replay(corpus, recovery_enabled=True, label="A")
    with (REPORTS_DIR / "runA.jsonl").open("w", encoding="utf-8") as f:
        for r in run_a:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\n=== run B (recovery=False) ===")
    run_b = run_replay(corpus, recovery_enabled=False, label="B")
    with (REPORTS_DIR / "runB.jsonl").open("w", encoding="utf-8") as f:
        for r in run_b:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\nГотово. Результаты в reports/runA.jsonl и reports/runB.jsonl")


if __name__ == "__main__":
    main()
