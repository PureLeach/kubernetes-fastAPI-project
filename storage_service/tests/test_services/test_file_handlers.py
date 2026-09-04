"""On-disk snapshot: atomicity, tolerance and round-tripping."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import orjson
import pytest

from storage_service.services.file_handlers import restore_snapshot, save_snapshot
from storage_service.services.storage import SNAPSHOT_VERSION, JsonObjectStorage

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.asyncio
async def test_save_writes_a_versioned_document(storage: JsonObjectStorage, snapshot_path: Path):
    """The snapshot carries a version so an incompatible layout can be detected."""
    await storage.set('k', {'v': 1})

    await save_snapshot(storage, snapshot_path)

    document = orjson.loads(snapshot_path.read_bytes())
    assert document['version'] == SNAPSHOT_VERSION
    assert document['entries']['k']['object'] == {'v': 1}


@pytest.mark.asyncio
async def test_save_creates_missing_parent_directories(storage: JsonObjectStorage, tmp_path: Path):
    """A volume mounted at a path that does not exist yet is created, not fatal."""
    path = tmp_path / 'deeply' / 'nested' / 'data.json'
    await storage.set('k', {'v': 1})

    await save_snapshot(storage, path)

    assert path.exists()


@pytest.mark.asyncio
async def test_save_leaves_no_temp_file_behind(storage: JsonObjectStorage, snapshot_path: Path):
    """The atomic write cleans up after itself; only the final file remains."""
    await storage.set('k', {'v': 1})

    await save_snapshot(storage, snapshot_path)

    assert [p.name for p in snapshot_path.parent.iterdir()] == [snapshot_path.name]


@pytest.mark.asyncio
async def test_save_on_empty_storage_overwrites_a_stale_snapshot(
    storage: JsonObjectStorage,
    snapshot_path: Path,
):
    """An emptied storage must not leave old objects on disk to be resurrected."""
    await storage.set('k', {'v': 1})
    await save_snapshot(storage, snapshot_path)
    await storage.clear()

    await save_snapshot(storage, snapshot_path)

    assert orjson.loads(snapshot_path.read_bytes())['entries'] == {}


@pytest.mark.asyncio
async def test_round_trip_preserves_objects_and_deadlines(snapshot_path: Path):
    """Saving and restoring returns the same objects with their deadlines intact."""
    source = JsonObjectStorage()
    await source.set('plain', {'a': 1})
    await source.set('ttl', {'b': 2}, ttl=600)
    expected = await source.snapshot()

    await save_snapshot(source, snapshot_path)
    target = JsonObjectStorage()
    await restore_snapshot(target, snapshot_path)

    restored = await target.snapshot()
    assert restored.keys() == expected.keys()
    assert restored['plain'] == expected['plain']
    restored_deadline = restored['ttl']['expires_at']
    expected_deadline = expected['ttl']['expires_at']
    assert restored_deadline is not None
    assert expected_deadline is not None
    assert abs(restored_deadline - expected_deadline) <= 1


@pytest.mark.asyncio
async def test_restore_removes_the_file_once_consumed(
    storage: JsonObjectStorage,
    snapshot_path: Path,
):
    """A successfully consumed snapshot is deleted so it cannot be replayed."""
    await storage.set('k', {'v': 1})
    await save_snapshot(storage, snapshot_path)

    await restore_snapshot(JsonObjectStorage(), snapshot_path)

    assert not snapshot_path.exists()


@pytest.mark.asyncio
async def test_restore_when_file_missing_is_a_no_op(
    storage: JsonObjectStorage,
    snapshot_path: Path,
):
    """The first ever start has no snapshot; that is normal, not an error."""
    await restore_snapshot(storage, snapshot_path)

    assert await storage.snapshot() == {}


@pytest.mark.asyncio
async def test_restore_keeps_an_unparsable_file(storage: JsonObjectStorage, snapshot_path: Path):
    """A corrupted snapshot stays on disk so the failure remains diagnosable."""
    snapshot_path.write_text('this is not json {{{')

    await restore_snapshot(storage, snapshot_path)

    assert snapshot_path.exists()
    assert await storage.snapshot() == {}


@pytest.mark.asyncio
async def test_restore_rejects_an_unknown_version(storage: JsonObjectStorage, snapshot_path: Path):
    """A snapshot written by a future version is refused rather than misread."""
    snapshot_path.write_bytes(orjson.dumps({'version': SNAPSHOT_VERSION + 1, 'entries': {'k': {}}}))

    await restore_snapshot(storage, snapshot_path)

    assert snapshot_path.exists()
    assert await storage.snapshot() == {}


@pytest.mark.asyncio
async def test_restore_tolerates_a_structurally_broken_entry(
    storage: JsonObjectStorage,
    snapshot_path: Path,
):
    """One bad entry must not cost the good ones, nor raise during startup."""
    snapshot_path.write_bytes(
        orjson.dumps(
            {
                'version': SNAPSHOT_VERSION,
                'entries': {
                    'good': {'object': {'v': 1}, 'expires_at': None},
                    'bad': {'object': 'not-a-mapping'},
                },
            },
        ),
    )

    await restore_snapshot(storage, snapshot_path)

    assert set(await storage.snapshot()) == {'good'}


@pytest.mark.asyncio
async def test_restore_drops_entries_that_expired_while_down(
    storage: JsonObjectStorage,
    snapshot_path: Path,
):
    """Downtime counts against a TTL — an object cannot outlive its deadline."""
    snapshot_path.write_bytes(
        orjson.dumps(
            {
                'version': SNAPSHOT_VERSION,
                'entries': {'stale': {'object': {'v': 1}, 'expires_at': time.time() - 1}},
            },
        ),
    )

    await restore_snapshot(storage, snapshot_path)

    assert await storage.snapshot() == {}
