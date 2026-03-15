"""
Benchmark different embedding models for Russian legal retrieval.

Usage:
    cd backend
    EMBEDDING_MODEL=BAAI/bge-m3 python scripts/eval_embeddings.py
    EMBEDDING_MODEL=intfloat/multilingual-e5-base python scripts/eval_embeddings.py
    EMBEDDING_MODEL=ai-forever/sbert_large_nlu_ru python scripts/eval_embeddings.py
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------------------
# Test cases: query → expected article number (as string)
# Each case is a realistic user question from Russian legal practice.
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "query": "Как расторгнуть договор по инициативе одной стороны?",
        "expected_article": "450",
        "law": "ГК РФ",
    },
    {
        "query": "Какой общий срок исковой давности?",
        "expected_article": "196",
        "law": "ГК РФ",
    },
    {
        "query": "Обязательства должны исполняться надлежащим образом",
        "expected_article": "309",
        "law": "ГК РФ",
    },
    {
        "query": "Права работника при увольнении по сокращению штата",
        "expected_article": "178",
        "law": "ТК РФ",
    },
    {
        "query": "Понятие договора купли-продажи",
        "expected_article": "454",
        "law": "ГК РФ",
    },
    {
        "query": "Дееспособность гражданина",
        "expected_article": "21",
        "law": "ГК РФ",
    },
    {
        "query": "Возмещение убытков при нарушении договора",
        "expected_article": "393",
        "law": "ГК РФ",
    },
    {
        "query": "Условия наступления материальной ответственности работника",
        "expected_article": "233",
        "law": "ТК РФ",
    },
]

# Small synthetic corpus — in production replace with real НПА chunks.
CORPUS: list[dict] = [
    {
        "article": "450",
        "law": "ГК РФ",
        "text": (
            "Статья 450. Основания изменения и расторжения договора\n"
            "1. Изменение и расторжение договора возможны по соглашению сторон, если иное "
            "не предусмотрено настоящим Кодексом, другими законами или договором.\n"
            "2. По требованию одной из сторон договор может быть изменён или расторгнут по "
            "решению суда только при существенном нарушении договора другой стороной."
        ),
    },
    {
        "article": "196",
        "law": "ГК РФ",
        "text": (
            "Статья 196. Общий срок исковой давности\n"
            "1. Общий срок исковой давности составляет три года со дня, определяемого в "
            "соответствии со статьёй 200 настоящего Кодекса."
        ),
    },
    {
        "article": "309",
        "law": "ГК РФ",
        "text": (
            "Статья 309. Общие положения\n"
            "Обязательства должны исполняться надлежащим образом в соответствии с условиями "
            "обязательства и требованиями закона, иных правовых актов, а при отсутствии таких "
            "условий и требований — в соответствии с обычаями или иными обычно предъявляемыми требованиями."
        ),
    },
    {
        "article": "178",
        "law": "ТК РФ",
        "text": (
            "Статья 178. Выходные пособия\n"
            "При расторжении трудового договора в связи с ликвидацией организации либо "
            "сокращением численности или штата работников организации увольняемому работнику "
            "выплачивается выходное пособие в размере среднего месячного заработка."
        ),
    },
    {
        "article": "454",
        "law": "ГК РФ",
        "text": (
            "Статья 454. Договор купли-продажи\n"
            "1. По договору купли-продажи одна сторона (продавец) обязуется передать вещь "
            "(товар) в собственность другой стороне (покупателю), а покупатель обязуется "
            "принять этот товар и уплатить за него определённую денежную сумму (цену)."
        ),
    },
    {
        "article": "21",
        "law": "ГК РФ",
        "text": (
            "Статья 21. Дееспособность гражданина\n"
            "1. Способность гражданина своими действиями приобретать и осуществлять "
            "гражданские права, создавать для себя гражданские обязанности и исполнять их "
            "(гражданская дееспособность) возникает в полном объёме с наступлением "
            "совершеннолетия, то есть по достижении восемнадцатилетнего возраста."
        ),
    },
    {
        "article": "393",
        "law": "ГК РФ",
        "text": (
            "Статья 393. Обязанность должника возместить убытки\n"
            "1. Должник обязан возместить кредитору убытки, причинённые неисполнением или "
            "ненадлежащим исполнением обязательства."
        ),
    },
    {
        "article": "233",
        "law": "ТК РФ",
        "text": (
            "Статья 233. Условия наступления материальной ответственности стороны трудового договора\n"
            "Материальная ответственность стороны трудового договора наступает за ущерб, "
            "причинённый ею другой стороне этого договора в результате её виновного "
            "противоправного поведения (действий или бездействия), если иное не предусмотрено "
            "настоящим Кодексом или иными федеральными законами."
        ),
    },
]


@dataclass
class EvalResult:
    model: str
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    avg_rank: float
    elapsed_s: float


def cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a, axis=-1, keepdims=True) + 1e-9)
    b_norm = b / (np.linalg.norm(b, axis=-1, keepdims=True) + 1e-9)
    return a_norm @ b_norm.T


def evaluate_model(model_name: str) -> EvalResult:
    from sentence_transformers import SentenceTransformer

    prefix = ""
    if "e5" in model_name.lower():
        prefix = "query: "

    print(f"\n  Loading {model_name}...")
    t0 = time.time()
    model = SentenceTransformer(model_name)

    corpus_texts = [c["text"] for c in CORPUS]
    corpus_embs = model.encode(corpus_texts, normalize_embeddings=True, show_progress_bar=False)

    hits_1 = hits_3 = hits_5 = 0
    ranks: list[int] = []

    for tc in TEST_CASES:
        q_text = prefix + tc["query"]
        q_emb = model.encode([q_text], normalize_embeddings=True, show_progress_bar=False)[0]
        sims = cosine_sim(q_emb[None, :], corpus_embs)[0]
        ranked_indices = np.argsort(sims)[::-1]

        for rank, idx in enumerate(ranked_indices):
            if CORPUS[idx]["article"] == tc["expected_article"]:
                ranks.append(rank + 1)
                if rank == 0:
                    hits_1 += 1
                if rank < 3:
                    hits_3 += 1
                if rank < 5:
                    hits_5 += 1
                break
        else:
            ranks.append(len(CORPUS) + 1)

    elapsed = time.time() - t0
    n = len(TEST_CASES)
    return EvalResult(
        model=model_name,
        hit_at_1=hits_1 / n,
        hit_at_3=hits_3 / n,
        hit_at_5=hits_5 / n,
        avg_rank=sum(ranks) / n,
        elapsed_s=elapsed,
    )


MODELS = [
    "BAAI/bge-m3",
    "intfloat/multilingual-e5-base",
    "ai-forever/sbert_large_nlu_ru",
]


def main() -> None:
    target = os.getenv("EMBEDDING_MODEL")
    models_to_eval = [target] if target else MODELS

    print(f"Evaluating {len(models_to_eval)} model(s) on {len(TEST_CASES)} legal queries...\n")
    print(f"{'Model':<45} {'H@1':>6} {'H@3':>6} {'H@5':>6} {'Avg rank':>9} {'Time(s)':>8}")
    print("-" * 85)

    results: list[EvalResult] = []
    for model_name in models_to_eval:
        try:
            r = evaluate_model(model_name)
            results.append(r)
            print(
                f"{r.model:<45} {r.hit_at_1:>6.0%} {r.hit_at_3:>6.0%} "
                f"{r.hit_at_5:>6.0%} {r.avg_rank:>9.1f} {r.elapsed_s:>8.1f}"
            )
        except Exception as exc:
            print(f"{model_name:<45} ERROR: {exc}")

    if results:
        best = max(results, key=lambda r: (r.hit_at_5, r.hit_at_3, r.hit_at_1))
        print(f"\nBest model: {best.model}  (H@5={best.hit_at_5:.0%})")


if __name__ == "__main__":
    main()
