"""Unified error responses for HTTP exceptions and unhandled errors."""

from __future__ import annotations

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from storage_service.api.middleware import REQUEST_ID_HEADER

logger = structlog.getLogger(__name__)


_STATUS_TO_CODE = {
    status.HTTP_400_BAD_REQUEST: 'bad_request',
    status.HTTP_404_NOT_FOUND: 'not_found',
    status.HTTP_409_CONFLICT: 'conflict',
    status.HTTP_413_CONTENT_TOO_LARGE: 'payload_too_large',
    status.HTTP_422_UNPROCESSABLE_CONTENT: 'unprocessable_entity',
    status.HTTP_500_INTERNAL_SERVER_ERROR: 'internal_error',
}


def _request_id(request: Request) -> str | None:
    return getattr(request.state, 'request_id', None)


def _envelope(
    *,
    status_code: int,
    code: str,
    message: str,
    request_id: str | None,
    details: object = None,
) -> JSONResponse:
    body: dict[str, object] = {'error': {'code': code, 'message': message, 'request_id': request_id}}
    if details is not None:
        body['error']['details'] = details  # type: ignore[index]
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return JSONResponse(status_code=status_code, content=body, headers=headers)


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = _STATUS_TO_CODE.get(exc.status_code, 'http_error')
    return _envelope(
        status_code=exc.status_code,
        code=code,
        message=str(exc.detail),
        request_id=_request_id(request),
    )


async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _envelope(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code='unprocessable_entity',
        message='Request payload failed validation.',
        request_id=_request_id(request),
        details=jsonable_encoder(exc.errors()),
    )


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception('unhandled_exception', error=str(exc))
    return _envelope(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code='internal_error',
        message='Internal server error.',
        request_id=_request_id(request),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_exception_handler)
