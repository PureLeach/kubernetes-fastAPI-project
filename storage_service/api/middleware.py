"""ASGI middleware: request-id propagation and structured access logging."""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import Request, Response

REQUEST_ID_HEADER = 'X-Request-ID'

logger = structlog.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Bind a per-request id into structlog contextvars and echo it as a header.

    The id comes from the inbound `X-Request-ID` header when present, otherwise
    a fresh UUID4 is generated. Every log line emitted while the request is in
    flight automatically carries `request_id` and `path`.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception('request_failed', duration_ms=round(duration_ms, 2))
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            'request_completed',
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
