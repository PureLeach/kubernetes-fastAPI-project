"""Unit tests for the shared FastAPI dependencies."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest
from fastapi import HTTPException, status

from storage_service.api.dependencies import enforce_payload_limit, get_storage

if TYPE_CHECKING:
    from fastapi import Request

    from storage_service.settings.core import Settings


def _request(settings: Settings, storage: object = None) -> Request:
    """A stand-in carrying only the app state the dependencies read."""
    return cast(
        'Request', SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings, storage=storage)))
    )


def test_get_storage_returns_the_apps_storage(settings: Settings):
    """The dependency reads app state rather than importing a global."""
    sentinel = object()

    assert get_storage(_request(settings, storage=sentinel)) is sentinel


@pytest.mark.asyncio
async def test_oversized_content_length_is_rejected(settings: Settings):
    """A declared length over the limit fails fast, before the body is read."""
    with pytest.raises(HTTPException) as excinfo:
        await enforce_payload_limit(_request(settings), content_length=settings.max_object_bytes + 1)

    assert excinfo.value.status_code == status.HTTP_413_CONTENT_TOO_LARGE


@pytest.mark.asyncio
@pytest.mark.parametrize('content_length', [None, 0, 1024], ids=['absent', 'empty', 'within-limit'])
async def test_acceptable_content_length_passes(settings: Settings, content_length: int | None):
    """A missing or in-range Content-Length is not the dependency's business."""
    await enforce_payload_limit(_request(settings), content_length=content_length)
