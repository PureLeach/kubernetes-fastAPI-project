"""ASGI middleware: request-id propagation, access logging and body limits."""

from __future__ import annotations

import time
import uuid
from typing import TYPE_CHECKING

import structlog
from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import Request, Response
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

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


class BodySizeLimitMiddleware:
    """
    Abort requests whose body exceeds `max_bytes`, counted as it streams in.

    `enforce_payload_limit` rejects on `Content-Length`, but that header is the
    client's word: a chunked request carries none and would slip past. Counting
    the bytes that actually arrive holds the limit either way. Raising keeps the
    failure on the normal exception path, so it reuses the 413 envelope.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message['type'] == 'http.request':
                received += len(message.get('body', b''))
                if received > self.max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f'Payload too large (limit {self.max_bytes} bytes).',
                    )
            return message

        await self.app(scope, limited_receive, send)
