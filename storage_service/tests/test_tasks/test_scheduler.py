"""The background snapshot job and its scheduler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from storage_service.services.storage import JsonObjectStorage
from storage_service.settings.core import Settings
from storage_service.tasks.scheduler import SNAPSHOT_JOB_ID, build_scheduler
from storage_service.tasks.snapshot import periodic_snapshot

if TYPE_CHECKING:
    from pathlib import Path


def _settings(tmp_path: Path, interval: int) -> Settings:
    return Settings(
        _env_file=None,
        objects_data_path=tmp_path / 'data.json',
        snapshot_interval_seconds=interval,
    )


def test_scheduler_is_disabled_by_a_zero_interval(tmp_path: Path):
    """Setting the interval to 0 turns the job off rather than scheduling it."""
    assert build_scheduler(storage=JsonObjectStorage(), settings=_settings(tmp_path, 0)) is None


@pytest.mark.asyncio
async def test_scheduler_registers_the_snapshot_job(tmp_path: Path):
    """A positive interval yields a scheduler carrying exactly the snapshot job."""
    scheduler = build_scheduler(storage=JsonObjectStorage(), settings=_settings(tmp_path, 30))

    assert scheduler is not None
    job = scheduler.get_job(SNAPSHOT_JOB_ID)
    assert job is not None
    assert job.trigger.interval.total_seconds() == 30


@pytest.mark.asyncio
async def test_periodic_snapshot_writes_the_file(tmp_path: Path):
    """The job flushes the storage it was bound to."""
    storage = JsonObjectStorage()
    await storage.set('k', {'v': 1})
    path = tmp_path / 'data.json'

    await periodic_snapshot(storage, path)

    assert path.exists()


@pytest.mark.asyncio
async def test_periodic_snapshot_never_raises(tmp_path: Path):
    """A failing write is logged, not raised: raising would drop the schedule."""
    storage = JsonObjectStorage()
    await storage.set('k', {'v': 1})
    unwritable = tmp_path / 'a-file'
    unwritable.write_text('not a directory')

    await periodic_snapshot(storage, unwritable / 'nested' / 'data.json')


def test_application_runs_and_stops_the_scheduler(tmp_path: Path):
    """A configured interval means the app starts the job and shuts it down cleanly."""
    from fastapi.testclient import TestClient

    from storage_service.main import create_app

    app = create_app(settings=_settings(tmp_path, 30), storage=JsonObjectStorage())
    with TestClient(app) as client:
        assert client.get('/probes/liveness').status_code == 200
