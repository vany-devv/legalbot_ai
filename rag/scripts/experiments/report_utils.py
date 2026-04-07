"""Shared utilities for experiment reports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def save_json(data: dict | list, path: Path) -> None:
    """Write *data* as pretty-printed JSON (UTF-8, no ASCII escaping)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"  → JSON saved: {path}")


def save_markdown(title: str, sections: list[tuple[str, str]], path: Path) -> None:
    """Write a Markdown report with *title* and a list of (heading, body) sections."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {title}",
        "",
        f"*Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
    ]
    for heading, body in sections:
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(body.strip())
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → Report saved: {path}")


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Build a Markdown table from *headers* and *rows*."""
    sep = ["-" * max(len(h), 3) for h in headers]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def print_summary(metrics: dict[str, tuple[float, float, bool]]) -> None:
    """Print pass/fail summary to console.

    *metrics*: {name: (value, threshold, passed)}
    """
    print()
    print("=" * 60)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 60)
    all_passed = True
    for name, (value, threshold, passed) in metrics.items():
        mark = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {value:.2%}  (порог: {threshold:.0%})  {mark}")
        if not passed:
            all_passed = False
    print("-" * 60)
    verdict = "✅ ГИПОТЕЗА ПОДТВЕРЖДЕНА" if all_passed else "❌ ГИПОТЕЗА НЕ ПОДТВЕРЖДЕНА"
    print(f"  {verdict}")
    print("=" * 60)
    print()
