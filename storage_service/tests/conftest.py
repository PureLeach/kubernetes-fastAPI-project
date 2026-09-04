"""
Fixtures building an isolated application per test.

Each test gets its own settings, storage and snapshot file under `tmp_path`,
so nothing touches the process-wide singletons or the repository's `mnt/`.
`_env_file=None` keeps a local `.env` out of the run.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from storage_service.main import create_app
from storage_service.services.storage import JsonObjectStorage
from storage_service.settings.core import Settings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from fastapi import FastAPI


@pytest.fixture
def snapshot_path(tmp_path: Path) -> Path:
    return tmp_path / 'data.json'


@pytest.fixture
def settings(snapshot_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        objects_data_path=snapshot_path,
        snapshot_interval_seconds=0,
        enable_metrics=True,
    )


@pytest.fixture
def storage() -> JsonObjectStorage:
    return JsonObjectStorage()


@pytest.fixture
def app(settings: Settings, storage: JsonObjectStorage) -> FastAPI:
    return create_app(settings=settings, storage=storage)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """A client that runs the lifespan, so snapshot restore/save happen."""
    with TestClient(app) as test_client:
        yield test_client
