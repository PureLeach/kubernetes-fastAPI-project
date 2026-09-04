"""The snapshot round-trip as the application actually performs it."""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson
from fastapi import status
from fastapi.testclient import TestClient

from storage_service.main import create_app
from storage_service.services.storage import JsonObjectStorage

if TYPE_CHECKING:
    from pathlib import Path

    from storage_service.settings.core import Settings


def test_objects_survive_a_restart(settings: Settings, snapshot_path: Path):
    """Shutdown writes the snapshot and the next startup reads it back."""
    with TestClient(create_app(settings=settings, storage=JsonObjectStorage())) as first:
        assert first.put('/v1/objects/persisted', json={'v': 1}).status_code == status.HTTP_201_CREATED
    assert snapshot_path.exists(), 'shutdown should have written a snapshot'

    with TestClient(create_app(settings=settings, storage=JsonObjectStorage())) as second:
        assert not snapshot_path.exists(), 'a consumed snapshot should not be replayable'
        response = second.get('/v1/objects/persisted')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'v': 1}


def test_injected_storage_is_the_one_that_gets_persisted(
    settings: Settings,
    snapshot_path: Path,
):
    """The lifespan snapshots the injected storage, not the module singleton."""
    injected = JsonObjectStorage()

    with TestClient(create_app(settings=settings, storage=injected)) as client:
        client.put('/v1/objects/mine', json={'v': 1})

    assert set(orjson.loads(snapshot_path.read_bytes())['entries']) == {'mine'}


def test_startup_survives_a_corrupted_snapshot(settings: Settings, snapshot_path: Path):
    """A broken snapshot must not put the pod into a restart loop."""
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text('{ this is not valid json')

    with TestClient(create_app(settings=settings, storage=JsonObjectStorage())) as client:
        assert client.get('/probes/readiness').status_code == status.HTTP_200_OK
        assert client.get('/v1/objects/anything').status_code == status.HTTP_404_NOT_FOUND
