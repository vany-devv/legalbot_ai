"""Серверная генерация премиального PDF-отчёта анализа рекламы.

Go-api дёргает POST /report/pdf с JSON сохранённого анализа → Jinja2-шаблон
→ WeasyPrint (HTML+CSS → векторный PDF). Один фирменный шаблон LegalBot.
"""
from __future__ import annotations

import html
import logging
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import Response
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/report", tags=["report"])

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "report"
_jinja = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

_RISK_LABEL = {"high": "Высокий", "medium": "Средний", "low": "Низкий"}


# ─── Входная модель (то, что собирает Go из GetResponse) ──────────────
class _Risk(BaseModel):
    model_config = ConfigDict(extra="ignore")
    fragment: str = ""
    law_reference: str = ""
    risk_level: str = "medium"
    description: str = ""
    suggestion: str = ""


class _Result(BaseModel):
    model_config = ConfigDict(extra="ignore")
    risks: list[_Risk] = []
    summary: str = ""
    overall_risk_level: str = "unknown"


class _Citation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    content: str = ""
    meta: dict = {}


class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str = ""
    ad_text: str = ""
    created_at: str = ""
    result: _Result = _Result()
    citations: list[_Citation] = []


def _annotate(ad_text: str, risks: list[_Risk]) -> str:
    """HTML-экранирует материал и подсвечивает фрагменты рисков <mark>+бейдж.

    Простое регистронезависимое вхождение первого совпадения (для отчёта
    достаточно — это presentation, не аналитика). Не нашли → без подсветки,
    риск всё равно попадёт в §3.
    """
    escaped = html.escape(ad_text)
    for idx, risk in enumerate(risks, 1):
        frag = (risk.fragment or "").strip()
        if not frag or frag == "[отсутствует в материале]":
            continue
        frag_esc = html.escape(frag)
        m = re.search(re.escape(frag_esc), escaped, re.IGNORECASE)
        if not m:
            continue
        level = risk.risk_level if risk.risk_level in _RISK_LABEL else "medium"
        repl = (
            f'<mark class="mk mk-{level}">{m.group(0)}'
            f'<sup class="mk-n">{idx}</sup></mark>'
        )
        escaped = escaped[: m.start()] + repl + escaped[m.end():]
    return escaped


def _score(counts: dict, has_risks: bool) -> dict:
    """Рейтинг документа 1:1 с фронтом (analyze/index.vue): 10 − штрафы,
    clamp[0,10], одна десятичная. Категория-бейдж выводится ИЗ ЧИСЛА (а не из
    raw overall_risk_level LLM) — чтобы формулировка не противоречила оценке
    (7.0 не должен называться «Высокий риск»)."""
    raw = 10 - counts["high"] * 1.5 - counts["medium"] * 0.8 - counts["low"] * 0.3
    s = max(0.0, min(10.0, raw))
    if not has_risks:
        cls, lvl, label = "sc-ok", "none", "Нарушений не выявлено"
    elif s < 4:
        cls, lvl, label = "sc-danger", "high", "Высокий риск нарушений"
    elif s < 6:
        cls, lvl, label = "sc-warning", "medium", "Существенный риск"
    elif s < 8:
        cls, lvl, label = "sc-amber", "low", "Умеренный риск"
    else:
        cls, lvl, label = "sc-ok", "none", "Низкий риск"
    return {"value": f"{s:.1f}", "cls": cls, "level": lvl, "label": label}


def _fmt_date(raw: str) -> str:
    if not raw:
        return datetime.now().strftime("%d.%m.%Y")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%d.%m.%Y")
    except ValueError:
        return raw[:10]


@router.post("/pdf")
async def generate_pdf(req: ReportRequest) -> Response:
    from weasyprint import HTML  # ленивый импорт — тяжёлый, нужен только тут

    risks = req.result.risks
    counts = {"high": 0, "medium": 0, "low": 0}
    for r in risks:
        counts[r.risk_level if r.risk_level in counts else "medium"] += 1

    sc = _score(counts, bool(risks))

    ctx = {
        # Косметика для legacy-анализов: убираем хвостовой маркер усечения "…"
        # (новые анализы сохраняются с полным заголовком, maxTitleChars=140).
        "title": (req.title or "Рекламный материал").rstrip("… ").rstrip("_ "),
        "date": _fmt_date(req.created_at),
        "annotated_html": _annotate(req.ad_text, risks),
        "risks": [
            {
                "n": i,
                "level": r.risk_level if r.risk_level in _RISK_LABEL else "medium",
                "level_label": _RISK_LABEL.get(r.risk_level, "Средний"),
                "law_reference": r.law_reference or "—",
                "fragment": r.fragment or "",
                "description": r.description or "",
                "suggestion": r.suggestion or "",
            }
            for i, r in enumerate(risks, 1)
        ],
        "summary": req.result.summary or "",
        "overall": sc["level"],
        "overall_label": sc["label"],
        "counts": counts,
        "total_risks": len(risks),
        "score": sc["value"],
        "score_cls": sc["cls"],
    }

    html_str = _jinja.get_template("report.html").render(**ctx)
    pdf_bytes = HTML(string=html_str, base_url=str(_TEMPLATES_DIR)).write_pdf()
    logger.info("report_generated", extra={"risks": len(risks), "bytes": len(pdf_bytes)})
    return Response(content=pdf_bytes, media_type="application/pdf")
