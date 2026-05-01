"""HTTP-middleware и обработчики исключений для FastAPI."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_setup import request_id_var

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Кладёт X-Request-ID в ContextVar и пишет http_request лог на каждый запрос."""

    async def dispatch(self, request: Request, call_next: Callable):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_var.set(rid)

        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            level = logging.INFO
            if status >= 500:
                level = logging.ERROR
            elif status >= 400:
                level = logging.WARNING
            logger.log(
                level,
                "http_request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status,
                    "duration_ms": duration_ms,
                    "remote_addr": request.client.host if request.client else "",
                },
            )
            request_id_var.reset(token)


def register_exception_handlers(app: FastAPI) -> None:
    """Глобальный обработчик: логирует необработанные исключения и возвращает 500 JSON."""

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        logger.exception(
            "unhandled_error",
            extra={"path": request.url.path, "method": request.method},
        )
        return JSONResponse(status_code=500, content={"detail": "internal server error"})
