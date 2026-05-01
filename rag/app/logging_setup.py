"""
Структурное логирование для RAG-сервиса.

- LOG_LEVEL  — debug|info|warning|error  (default: info)
- LOG_FORMAT — json|text                 (default: text если ENV=development, иначе json)

JsonFormatter автоматически подцепляет request_id из ContextVar — его проставляет
RequestContextMiddleware на каждый входящий запрос.
"""

from __future__ import annotations

import json
import logging
import os
from contextvars import ContextVar
from typing import Optional

# Глобальный ContextVar — хранит request_id текущей задачи.
# Доступен из любой корутины через `request_id_var.get()`.
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Стандартные поля LogRecord — всё остальное считаем "extra" и сериализуем в JSON.
_RESERVED = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "asctime", "taskName",
}


class JsonFormatter(logging.Formatter):
    """Сериализует LogRecord в JSON с request_id и пользовательскими полями."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = request_id_var.get()
        if rid:
            payload["request_id"] = rid

        # Достаём extra-поля, переданные в logger.info("event", extra={...})
        for k, v in record.__dict__.items():
            if k in _RESERVED or k.startswith("_"):
                continue
            payload[k] = v

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Человекочитаемый формат для локальной разработки. Включает request_id если есть."""

    def __init__(self) -> None:
        super().__init__("%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        rid = request_id_var.get()
        if rid:
            base = f"{base}  [rid={rid}]"
        return base


def configure(env: str = "") -> None:
    """Настраивает корневой логгер. Идемпотентно: чистит старые хендлеры."""
    level = _parse_level(os.getenv("LOG_LEVEL", "info"))
    fmt = os.getenv("LOG_FORMAT", "").lower()
    if not fmt:
        fmt = "text" if env.lower().startswith("dev") else "json"

    formatter: logging.Formatter
    formatter = JsonFormatter() if fmt == "json" else TextFormatter()

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Убираем дефолтный uvicorn.access — будет дублировать наш http_request лог.
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False
    # uvicorn.error оставляем — он пишет startup/shutdown и трейсы.
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True


def _parse_level(s: str) -> int:
    return {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "warn": logging.WARNING,
        "error": logging.ERROR,
    }.get(s.lower(), logging.INFO)
