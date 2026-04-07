"""Эксперимент Г1 — Гибридный поиск.

Проверяет гипотезу: модуль гибридного поиска (RRF-слияние HNSW pgvector +
PostgreSQL FTS) обеспечивает полноту лексического поиска ≥ 90% и полноту
семантического поиска ≥ 85% при p95 latency ≤ 500 мс.

Предварительные условия:
    - PostgreSQL с pgvector запущен и содержит ≥ 5 000 чанков
    - Credentials эмбеддера настроены в .env

Использование:
    # Сгенерировать шаблон запросов:
    python experiment_g1_search.py --generate-template

    # Запустить эксперимент:
    python experiment_g1_search.py --queries test_data/queries_g1.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.retrieval import HybridRetriever, SearchResult  # noqa: E402
from app.dependencies import _build_embedder  # noqa: E402
from app.storage.pgvector import VectorRepository, create_pool  # noqa: E402

from report_utils import md_table, print_summary, save_json, save_markdown  # noqa: E402

TOP_K = 5
LEXICAL_THRESHOLD = 0.90
SEMANTIC_THRESHOLD = 0.85
LATENCY_P95_THRESHOLD_MS = 500
LATENCY_RUNS = 200


def generate_template(output_path: Path) -> None:
    """Write a template for test queries."""
    template = {
        "lexical": [
            {"query": "статья 81 ТК РФ", "expected_law": "ТК РФ", "expected_article": "81",
             "description": "Точный запрос по реквизитам"},
            {"query": "пункт 3 статьи 450 ГК РФ", "expected_law": "ГК РФ", "expected_article": "450",
             "description": "Запрос по пункту статьи"},
        ],
        "semantic": [
            {"query": "основания увольнения по инициативе работодателя",
             "expected_law": "ТК РФ", "expected_article": "81",
             "description": "Семантический запрос на естественном языке"},
            {"query": "последствия существенного нарушения договора",
             "expected_law": "ГК РФ", "expected_article": "450",
             "description": "Семантический запрос"},
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Шаблон запросов: {output_path}")
    print("Заполни по 50 запросов в каждой группе (lexical, semantic).")
    print("Формат: query, expected_law, expected_article, description.")


def is_relevant(result: SearchResult, expected_law: str, expected_article: str) -> bool:
    """Check if a search result matches expected metadata."""
    meta = result.meta or {}
    article_match = str(meta.get("article", "")) == str(expected_article)
    law = str(meta.get("law", ""))
    law_match = expected_law.lower() in law.lower() or law.lower() in expected_law.lower()
    return article_match and law_match


async def run_experiment(queries_path: Path, output_dir: Path, database_url: str) -> None:
    queries_data = json.loads(queries_path.read_text(encoding="utf-8"))
    lexical_queries = queries_data.get("lexical", [])
    semantic_queries = queries_data.get("semantic", [])

    print(f"Лексических запросов: {len(lexical_queries)}")
    print(f"Семантических запросов: {len(semantic_queries)}")
    print()

    # Initialize
    print("Подключение к БД...")
    pool = await create_pool(database_url)
    embedder = _build_embedder()
    repo = VectorRepository(pool)
    retriever = HybridRetriever(repo, embedder)

    stats = await repo.get_stats()
    print(f"В базе: {stats['documents']} документов, {stats['chunks']} чанков")
    if stats["chunks"] < 5000:
        print(f"⚠️  Чанков ({stats['chunks']}) меньше порога 5000 — результаты могут быть нерепрезентативны")
    print()

    all_queries = (
        [("lexical", q) for q in lexical_queries]
        + [("semantic", q) for q in semantic_queries]
    )

    query_results = []

    # Pre-embed all queries (cache embeddings for latency measurement)
    print("Эмбеддинг запросов...")
    embeddings_cache: dict[str, np.ndarray] = {}
    for _, q in all_queries:
        query_text = q["query"]
        if query_text not in embeddings_cache:
            embeddings_cache[query_text] = await embedder.embed_query(query_text)
    print(f"  Закешировано {len(embeddings_cache)} эмбеддингов")
    print()

    # Run search for each query in 3 modes
    print("Прогон запросов (hybrid / dense / sparse)...")
    for query_class, q in all_queries:
        query_text = q["query"]
        expected_law = q["expected_law"]
        expected_article = q["expected_article"]
        embedding = embeddings_cache[query_text]

        record = {
            "class": query_class,
            "query": query_text,
            "expected_law": expected_law,
            "expected_article": expected_article,
        }

        # Hybrid search
        t0 = time.perf_counter()
        hybrid_results = await retriever.search(query_text, top_k=TOP_K)
        hybrid_time = (time.perf_counter() - t0) * 1000

        hybrid_hit = any(is_relevant(r, expected_law, expected_article) for r in hybrid_results)
        hybrid_rank = next(
            (i + 1 for i, r in enumerate(hybrid_results) if is_relevant(r, expected_law, expected_article)),
            0,
        )

        # Dense-only
        dense_results = await repo.dense_search(embedding, top_k=TOP_K)
        dense_hit = any(is_relevant(r, expected_law, expected_article) for r in dense_results)
        dense_rank = next(
            (i + 1 for i, r in enumerate(dense_results) if is_relevant(r, expected_law, expected_article)),
            0,
        )

        # Sparse-only
        sparse_results = await repo.fts_search(query_text, top_k=TOP_K)
        sparse_hit = any(is_relevant(r, expected_law, expected_article) for r in sparse_results)
        sparse_rank = next(
            (i + 1 for i, r in enumerate(sparse_results) if is_relevant(r, expected_law, expected_article)),
            0,
        )

        record.update(
            hybrid_hit=hybrid_hit, hybrid_rank=hybrid_rank, hybrid_time_ms=round(hybrid_time, 1),
            dense_hit=dense_hit, dense_rank=dense_rank,
            sparse_hit=sparse_hit, sparse_rank=sparse_rank,
        )
        query_results.append(record)

        h_mark = "✅" if hybrid_hit else "❌"
        print(f"  {h_mark} [{query_class[:3]}] «{query_text[:50]}» → "
              f"hybrid:{hybrid_rank or '—'} dense:{dense_rank or '—'} sparse:{sparse_rank or '—'}")

    # Latency benchmark (hybrid only, cached embeddings)
    print()
    print(f"Замер latency ({LATENCY_RUNS} прогонов, hybrid)...")
    latencies = []
    queries_cycle = all_queries * ((LATENCY_RUNS // len(all_queries)) + 1)
    for i in range(LATENCY_RUNS):
        _, q = queries_cycle[i]
        t0 = time.perf_counter()
        await retriever.search(q["query"], top_k=TOP_K)
        latencies.append((time.perf_counter() - t0) * 1000)

    latencies_arr = np.array(latencies)
    latency_stats = {
        "p50_ms": round(float(np.percentile(latencies_arr, 50)), 1),
        "p95_ms": round(float(np.percentile(latencies_arr, 95)), 1),
        "p99_ms": round(float(np.percentile(latencies_arr, 99)), 1),
        "mean_ms": round(float(np.mean(latencies_arr)), 1),
        "max_ms": round(float(np.max(latencies_arr)), 1),
        "min_ms": round(float(np.min(latencies_arr)), 1),
        "runs": LATENCY_RUNS,
    }
    print(f"  p50={latency_stats['p50_ms']}ms  p95={latency_stats['p95_ms']}ms  "
          f"p99={latency_stats['p99_ms']}ms  max={latency_stats['max_ms']}ms")

    await pool.close()

    # Compute metrics
    def compute_metrics(results: list[dict], mode: str) -> dict:
        hit_key = f"{mode}_hit"
        rank_key = f"{mode}_rank"
        hits = sum(1 for r in results if r[hit_key])
        total = len(results)
        completeness = hits / max(total, 1)
        ranks = [1.0 / r[rank_key] for r in results if r[rank_key] > 0]
        mrr = sum(ranks) / max(total, 1)
        return {"completeness": round(completeness, 4), "mrr": round(mrr, 4), "hits": hits, "total": total}

    lex_results = [r for r in query_results if r["class"] == "lexical"]
    sem_results = [r for r in query_results if r["class"] == "semantic"]

    metrics_table = {}
    for mode in ("hybrid", "dense", "sparse"):
        metrics_table[mode] = {
            "lexical": compute_metrics(lex_results, mode),
            "semantic": compute_metrics(sem_results, mode),
            "all": compute_metrics(query_results, mode),
        }

    lex_completeness = metrics_table["hybrid"]["lexical"]["completeness"]
    sem_completeness = metrics_table["hybrid"]["semantic"]["completeness"]
    p95 = latency_stats["p95_ms"]

    lex_passed = lex_completeness >= LEXICAL_THRESHOLD
    sem_passed = sem_completeness >= SEMANTIC_THRESHOLD
    latency_passed = p95 <= LATENCY_P95_THRESHOLD_MS

    summary = {
        "lexical_completeness": lex_completeness,
        "lexical_threshold": LEXICAL_THRESHOLD,
        "lexical_passed": lex_passed,
        "semantic_completeness": sem_completeness,
        "semantic_threshold": SEMANTIC_THRESHOLD,
        "semantic_passed": sem_passed,
        "p95_latency_ms": p95,
        "latency_threshold_ms": LATENCY_P95_THRESHOLD_MS,
        "latency_passed": latency_passed,
        "hypothesis_confirmed": lex_passed and sem_passed and latency_passed,
        "corpus_chunks": stats["chunks"],
        "corpus_documents": stats["documents"],
        "top_k": TOP_K,
    }

    full_results = {
        "summary": summary,
        "metrics_by_mode": metrics_table,
        "latency": latency_stats,
        "queries": query_results,
    }
    save_json(full_results, output_dir / "results_g1.json")

    # Markdown report
    summary_md = md_table(
        ["Метрика", "Значение", "Порог", "Результат"],
        [
            ["Полнота лексического поиска (hybrid)", f"{lex_completeness:.1%}", f"{LEXICAL_THRESHOLD:.0%}",
             "✅ PASS" if lex_passed else "❌ FAIL"],
            ["Полнота семантического поиска (hybrid)", f"{sem_completeness:.1%}", f"{SEMANTIC_THRESHOLD:.0%}",
             "✅ PASS" if sem_passed else "❌ FAIL"],
            ["p95 latency поиска", f"{p95:.0f} мс", f"{LATENCY_P95_THRESHOLD_MS} мс",
             "✅ PASS" if latency_passed else "❌ FAIL"],
        ],
    )

    comparison_rows = []
    for mode in ("hybrid", "dense", "sparse"):
        m = metrics_table[mode]
        comparison_rows.append([
            mode,
            f"{m['lexical']['completeness']:.1%}",
            f"{m['lexical']['mrr']:.3f}",
            f"{m['semantic']['completeness']:.1%}",
            f"{m['semantic']['mrr']:.3f}",
        ])
    comparison_md = md_table(
        ["Режим", "Лекс. полнота", "Лекс. MRR", "Сем. полнота", "Сем. MRR"],
        comparison_rows,
    )

    latency_md = md_table(
        ["Метрика", "Значение (мс)"],
        [
            ["p50", latency_stats["p50_ms"]],
            ["p95", latency_stats["p95_ms"]],
            ["p99", latency_stats["p99_ms"]],
            ["mean", latency_stats["mean_ms"]],
            ["max", latency_stats["max_ms"]],
            ["min", latency_stats["min_ms"]],
            ["runs", latency_stats["runs"]],
        ],
    )

    # Per-query detail (first 30 to keep report readable)
    detail_rows = []
    for r in query_results[:50]:
        h = "✅" if r["hybrid_hit"] else "❌"
        d = "✅" if r["dense_hit"] else "❌"
        s = "✅" if r["sparse_hit"] else "❌"
        detail_rows.append([
            r["class"][:3],
            r["query"][:60],
            f"ст.{r['expected_article']} {r['expected_law']}",
            f"{h} ранг:{r['hybrid_rank'] or '—'}",
            f"{d} ранг:{r['dense_rank'] or '—'}",
            f"{s} ранг:{r['sparse_rank'] or '—'}",
        ])
    detail_md = md_table(
        ["Класс", "Запрос", "Ожидаемое", "Hybrid", "Dense", "Sparse"],
        detail_rows,
    )

    verdict = ("✅ **ГИПОТЕЗА Г1 ПОДТВЕРЖДЕНА**" if summary["hypothesis_confirmed"]
               else "❌ **ГИПОТЕЗА Г1 НЕ ПОДТВЕРЖДЕНА**")

    save_markdown(
        "Отчёт эксперимента Г1 — Гибридный поиск",
        [
            ("Вердикт", verdict),
            ("Сводка метрик", summary_md),
            ("Сравнение режимов (hybrid / dense / sparse)", comparison_md),
            ("Latency (hybrid)", latency_md),
            ("Детализация по запросам", detail_md),
            ("Параметры эксперимента",
             f"- Корпус: {stats['documents']} документов, {stats['chunks']} чанков\n"
             f"- top_k: {TOP_K}\n"
             f"- Лексических запросов: {len(lex_results)}\n"
             f"- Семантических запросов: {len(sem_results)}\n"
             f"- Latency runs: {LATENCY_RUNS}\n"
             f"- Порог лексической полноты: {LEXICAL_THRESHOLD:.0%}\n"
             f"- Порог семантической полноты: {SEMANTIC_THRESHOLD:.0%}\n"
             f"- Порог p95 latency: {LATENCY_P95_THRESHOLD_MS} мс"),
        ],
        output_dir / "report_g1.md",
    )

    print_summary({
        "Полнота лексического (hybrid)": (lex_completeness, LEXICAL_THRESHOLD, lex_passed),
        "Полнота семантического (hybrid)": (sem_completeness, SEMANTIC_THRESHOLD, sem_passed),
        "p95 latency": (p95 / 1000, LATENCY_P95_THRESHOLD_MS / 1000, latency_passed),
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="Эксперимент Г1 — Гибридный поиск")
    parser.add_argument("--queries", type=Path, help="JSON с тестовыми запросами")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "reports", help="Папка для отчётов")
    parser.add_argument("--database-url", type=str, default=settings.database_url, help="PostgreSQL URL")
    parser.add_argument("--generate-template", action="store_true", help="Сгенерировать шаблон запросов")
    args = parser.parse_args()

    if args.generate_template:
        output = args.queries or (Path(__file__).parent / "test_data" / "queries_g1.json")
        generate_template(output)
        return

    if not args.queries:
        parser.error("Укажи --queries или --generate-template")

    asyncio.run(run_experiment(args.queries, args.output_dir, args.database_url))


if __name__ == "__main__":
    main()
