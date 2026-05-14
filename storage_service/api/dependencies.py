"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Header, HTTPException, Request, status

from storage_service.services.storage import JsonObjectStorage  # noqa: TC001 — runtime needed by FastAPI DI

if TYPE_CHECKING:
    from storage_service.settings.core import Settings


def get_storage(request: Request) -> JsonObjectStorage:
    """Return the storage instance attached to the running app."""
    return request.app.state.storage


async def enforce_payload_limit(
    request: Request,
    content_length: Annotated[int | None, Header()] = None,
) -> None:
    """Reject requests whose declared body size exceeds `max_object_bytes`."""
    settings: Settings = request.app.state.settings
    if content_length is not None and content_length > settings.max_object_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f'Payload too large (limit {settings.max_object_bytes} bytes).',
        )
