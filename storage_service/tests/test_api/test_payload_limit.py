"""The payload limit holds regardless of what the client declares."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from storage_service.main import create_app
from storage_service.services.storage import JsonObjectStorage
from storage_service.settings.core import Settings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

LIMIT_BYTES = 256


@pytest.fixture
def limited_client(tmp_path: Path) -> Iterator[TestClient]:
    """An app that accepts bodies no larger than `LIMIT_BYTES`."""
    settings = Settings(
        _env_file=None,
        max_object_bytes=LIMIT_BYTES,
        enable_metrics=False,
        snapshot_interval_seconds=0,
        objects_data_path=tmp_path / 'data.json',
    )
    with TestClient(create_app(settings=settings, storage=JsonObjectStorage())) as client:
        yield client


def test_payload_within_limit_succeeds(limited_client: TestClient):
    """A small body is accepted under the configured limit."""
    assert limited_client.put('/v1/objects/small', json={'ok': True}).status_code == status.HTTP_201_CREATED


def test_oversized_content_length_is_rejected(limited_client: TestClient):
    """A declared body over the limit is refused before it is read."""
    response = limited_client.put('/v1/objects/big', json={'k': 'x' * (LIMIT_BYTES * 4)})

    assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
    assert response.json()['error']['code'] == 'payload_too_large'


def test_oversized_chunked_body_is_rejected(limited_client: TestClient):
    """A chunked request declares no length, so the arriving bytes are counted."""

    def chunks() -> Iterator[bytes]:
        yield b'{"k": "'
        for _ in range(10):
            yield b'x' * LIMIT_BYTES
        yield b'"}'

    response = limited_client.put(
        '/v1/objects/chunked',
        content=chunks(),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
    assert response.json()['error']['code'] == 'payload_too_large'


def test_chunked_body_within_limit_succeeds(limited_client: TestClient):
    """Streaming itself is fine; only crossing the limit is not."""

    def chunks() -> Iterator[bytes]:
        yield b'{"ok":'
        yield b' true}'

    response = limited_client.put(
        '/v1/objects/streamed',
        content=chunks(),
        headers={'Content-Type': 'application/json'},
    )

    assert response.status_code == status.HTTP_201_CREATED
