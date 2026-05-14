import pytest
from fastapi import status
from fastapi.testclient import TestClient

from storage_service.main import create_app
from storage_service.services.storage import JsonObjectStorage
from storage_service.settings.core import Settings


def _build_app(*, max_object_bytes: int, tmp_path) -> TestClient:
    settings = Settings(
        max_object_bytes=max_object_bytes,
        enable_metrics=False,
        objects_data_path=tmp_path / 'data.json',
    )
    app = create_app(settings=settings, storage=JsonObjectStorage())
    return TestClient(app)


@pytest.mark.asyncio
async def test_payload_too_large_returns_413(tmp_path):
    """An oversized body is rejected with a structured 413 envelope."""
    client = _build_app(max_object_bytes=64, tmp_path=tmp_path)

    big_payload = {'k': 'x' * 1024}
    response = client.put('/v1/objects/big', json=big_payload)

    assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
    body = response.json()
    assert body['error']['code'] == 'payload_too_large'


@pytest.mark.asyncio
async def test_payload_within_limit_succeeds(tmp_path):
    """A small payload is accepted under the same configured limit."""
    client = _build_app(max_object_bytes=4096, tmp_path=tmp_path)

    response = client.put('/v1/objects/small', json={'ok': True})

    assert response.status_code == status.HTTP_201_CREATED
