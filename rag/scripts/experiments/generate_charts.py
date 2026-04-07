#!/usr/bin/env python3
"""Генерация графиков из результатов экспериментов Г1, Г2, Г3.

Использование:
    cd rag
    uv run python scripts/experiments/generate_charts.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

REPORTS = Path(__file__).parent / "reports"

# ── Настройки стиля ──────────────────────────────────────────────────────

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "#fafafa",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
})

COLORS = {
    "hybrid": "#2563eb",
    "dense": "#7c3aed",
    "sparse": "#dc2626",
    "pass": "#16a34a",
    "fail": "#dc2626",
    "neutral": "#6b7280",
    "bar1": "#2563eb",
    "bar2": "#7c3aed",
}


def load_json(name: str) -> dict:
    with open(REPORTS / name, encoding="utf-8") as f:
        return json.load(f)


# ── График 1: Сравнение Recall@5 по трем режимам ────────────────────────

def chart_recall_comparison(g1: dict) -> None:
    modes = g1["metrics_by_mode"]

    labels = ["Hybrid", "Dense", "Sparse"]
    lex = [modes[m]["lexical"]["completeness"] * 100 for m in ("hybrid", "dense", "sparse")]
    sem = [modes[m]["semantic"]["completeness"] * 100 for m in ("hybrid", "dense", "sparse")]

    x = np.arange(len(labels))
    w = 0.32

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars1 = ax.bar(x - w/2, lex, w, label="Лексические запросы", color=COLORS["bar1"], zorder=3)
    bars2 = ax.bar(x + w/2, sem, w, label="Семантические запросы", color=COLORS["bar2"], zorder=3)

    # Пороги
    ax.axhline(90, color=COLORS["bar1"], linestyle=":", alpha=0.6, linewidth=1)
    ax.axhline(85, color=COLORS["bar2"], linestyle=":", alpha=0.6, linewidth=1)
    ax.text(2.55, 90.5, "порог 90%", fontsize=8, color=COLORS["bar1"], alpha=0.7)
    ax.text(2.55, 85.5, "порог 85%", fontsize=8, color=COLORS["bar2"], alpha=0.7)

    # Подписи значений
    for bars in (bars1, bars2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 1, f"{h:.0f}%",
                    ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_ylabel("Recall@5, %")
    ax.set_title("Г1: Полнота поиска по режимам")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 105)
    ax.legend(loc="upper right", fontsize=9)

    fig.savefig(REPORTS / "chart_g1_recall.png")
    plt.close(fig)
    print(f"  chart_g1_recall.png")


# ── График 2: Распределение латентности ──────────────────────────────────

def chart_latency(g1: dict) -> None:
    lat = g1["latency"]

    labels = ["min", "p50", "mean", "p95", "p99", "max"]
    values = [lat["min_ms"], lat["p50_ms"], lat["mean_ms"],
              lat["p95_ms"], lat["p99_ms"], lat["max_ms"]]
    threshold = 500

    colors = [COLORS["pass"] if v <= threshold else COLORS["fail"] for v in values]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, values, color=colors, alpha=0.8, zorder=3, width=0.55)

    ax.axhline(threshold, color=COLORS["fail"], linestyle="--", linewidth=1.5,
               label=f"порог p95 = {threshold} мс", zorder=2)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 12, f"{val:.0f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_ylabel("Время, мс")
    ax.set_title(f"Г1: Латентность гибридного поиска ({lat['runs']} прогонов)")
    ax.set_ylim(0, max(values) * 1.15)
    ax.legend(fontsize=9)

    fig.savefig(REPORTS / "chart_g1_latency.png")
    plt.close(fig)
    print(f"  chart_g1_latency.png")


# ── График 3: Корпус по числу чанков ─────────────────────────────────────

def chart_corpus(g2: dict) -> None:
    docs = g2["documents"]

    # Короткие названия
    short_names = []
    for d in docs:
        name = d["law_name"]
        # Обрезаем длинные названия
        if "Конституция" in name:
            short_names.append("Конституция")
        elif "74-ФЗ" in name:
            short_names.append("Водный кодекс")
        elif "200-ФЗ" in name:
            short_names.append("Лесной кодекс")
        elif "117-ФЗ" in name:
            short_names.append("НК ч.2")
        elif "1-ФЗ" in name:
            short_names.append("УИК")
        elif "21-ФЗ" in name:
            short_names.append("КАС")
        elif "138-ФЗ" in name:
            short_names.append("ГПК")
        elif "174-ФЗ" in name:
            short_names.append("УПК")
        elif "230-ФЗ" in name:
            short_names.append("ГК ч.4")
        elif "146-ФЗ" in name and "2001" in name:
            short_names.append("ГК ч.3")
        elif "61-ФЗ" in name:
            short_names.append("Таможенный")
        elif "188-ФЗ" in name:
            short_names.append("Жилищный")
        elif "190-ФЗ" in name:
            short_names.append("Градостроит.")
        elif "195-ФЗ" in name:
            short_names.append("КоАП")
        elif "197-ФЗ" in name:
            short_names.append("Трудовой")
        elif "145-ФЗ" in name:
            short_names.append("Бюджетный")
        elif "146-ФЗ" in name:
            short_names.append("НК ч.1")
        else:
            short_names.append(name[:20])

    chunks = [d["chunks"] for d in docs]

    # Сортируем по убыванию
    order = sorted(range(len(chunks)), key=lambda i: chunks[i], reverse=True)
    short_names = [short_names[i] for i in order]
    chunks = [chunks[i] for i in order]

    fig, ax = plt.subplots(figsize=(9, 7))
    bars = ax.barh(range(len(chunks)), chunks, color=COLORS["hybrid"], alpha=0.8, zorder=3)

    # Подписи значений
    for i, (bar, val) in enumerate(zip(bars, chunks)):
        ax.text(val + 80, bar.get_y() + bar.get_height()/2,
                f"{val:,}".replace(",", " "), va="center", fontsize=10)

    ax.set_yticks(range(len(short_names)))
    ax.set_yticklabels(short_names, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Количество чанков")
    ax.set_title(f"Г2: Корпус документов ({sum(chunks):,} чанков, {len(docs)} НПА)".replace(",", " "))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", " ")))

    fig.savefig(REPORTS / "chart_g2_corpus.png")
    plt.close(fig)
    print(f"  chart_g2_corpus.png")


# ── График 4: MRR по режимам ─────────────────────────────────────────────

def chart_mrr_comparison(g1: dict) -> None:
    modes = g1["metrics_by_mode"]

    labels = ["Hybrid", "Dense", "Sparse"]
    lex_mrr = [modes[m]["lexical"]["mrr"] for m in ("hybrid", "dense", "sparse")]
    sem_mrr = [modes[m]["semantic"]["mrr"] for m in ("hybrid", "dense", "sparse")]

    x = np.arange(len(labels))
    w = 0.32

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars1 = ax.bar(x - w/2, lex_mrr, w, label="Лексические запросы", color=COLORS["bar1"], zorder=3)
    bars2 = ax.bar(x + w/2, sem_mrr, w, label="Семантические запросы", color=COLORS["bar2"], zorder=3)

    for bars in (bars1, bars2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.01, f"{h:.3f}",
                    ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_ylabel("MRR@5")
    ax.set_title("Г1: Mean Reciprocal Rank по режимам")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper right", fontsize=9)

    fig.savefig(REPORTS / "chart_g1_mrr.png")
    plt.close(fig)
    print(f"  chart_g1_mrr.png")


# ── main ──────────────────────────────────────────────────────────────────

def main() -> None:
    print("Генерация графиков...\n")

    g1 = load_json("results_g1.json")
    g2 = load_json("results_g2.json")

    chart_recall_comparison(g1)
    chart_mrr_comparison(g1)
    chart_latency(g1)
    chart_corpus(g2)

    print(f"\nГотово! Графики сохранены в {REPORTS}/")


if __name__ == "__main__":
    main()
