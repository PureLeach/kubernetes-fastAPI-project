"""Kubernetes probe endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from storage_service.main import create_app
from storage_service.services.storage import JsonObjectStorage
from storage_service.settings.core import Settings

if TYPE_CHECKING:
    from pathlib import Path


def test_liveness_probe(client: TestClient):
    """Liveness answers "the process is serving" and carries no checks."""
    response = client.get('/probes/liveness')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'healthy': True, 'checks': []}


def test_readiness_probe(client: TestClient):
    """Readiness passes when the snapshot volume is present and writable."""
    response = client.get('/probes/readiness')

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body['healthy'] is True
    assert [check['name'] for check in body['checks']] == ['snapshot_dir_writable']


def test_readiness_fails_when_the_snapshot_volume_is_missing(tmp_path: Path):
    """A missing volume fails readiness but not liveness: a restart won't remount it."""
    settings = Settings(
        _env_file=None,
        enable_metrics=False,
        snapshot_interval_seconds=0,
        objects_data_path=tmp_path / 'never-mounted' / 'data.json',
    )
    app = create_app(settings=settings, storage=JsonObjectStorage())

    # No lifespan here: startup would create the directory.
    client = TestClient(app)

    assert client.get('/probes/readiness').status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert client.get('/probes/liveness').status_code == status.HTTP_200_OK


def test_readiness_fails_when_the_snapshot_volume_is_read_only(client: TestClient):
    """A volume that mounted read-only is just as unusable as one that is absent."""
    with patch('storage_service.settings.probes.os.access', return_value=False):
        response = client.get('/probes/readiness')

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()['checks'][0]['passed'] is False
