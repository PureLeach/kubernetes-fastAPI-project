"""Prometheus metrics exposition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import status
from fastapi.testclient import TestClient

from storage_service.main import create_app
from storage_service.services.storage import JsonObjectStorage

if TYPE_CHECKING:
    from pathlib import Path

    from storage_service.settings.core import Settings


def test_metrics_are_exposed(client: TestClient):
    """GET /metrics returns a Prometheus exposition payload."""
    response = client.get('/metrics')

    assert response.status_code == status.HTTP_200_OK
    assert response.headers['content-type'].startswith('text/plain')
    assert b'# HELP' in response.content


def test_metrics_can_be_switched_off(tmp_path: Path, settings: Settings):
    """`ENABLE_METRICS=false` leaves the endpoint unmounted entirely."""
    disabled = settings.model_copy(update={'enable_metrics': False})

    with TestClient(create_app(settings=disabled, storage=JsonObjectStorage())) as client:
        assert client.get('/metrics').status_code == status.HTTP_404_NOT_FOUND
