"""Unit tests for JsonObjectStorage."""

from __future__ import annotations

import asyncio
import time

import pytest

from storage_service.services.storage import JsonObjectStorage


@pytest.mark.asyncio
async def test_set_records_absolute_expiry():
    """A TTL is stored as a wall-clock deadline, not as the raw TTL."""
    storage = JsonObjectStorage()
    before = time.time()
    await storage.set('k', {'v': 1}, ttl=100)

    entry = (await storage.snapshot())['k']

    assert entry['object'] == {'v': 1}
    assert entry['expires_at'] is not None
    assert before + 100 <= entry['expires_at'] <= time.time() + 100


@pytest.mark.asyncio
async def test_set_without_ttl_never_expires():
    """An object stored without `expires` carries a null deadline."""
    storage = JsonObjectStorage()
    await storage.set('k', {'v': 1})

    assert (await storage.snapshot())['k']['expires_at'] is None


@pytest.mark.asyncio
async def test_get_returns_none_after_expiry():
    """Reading a key past its deadline returns None and forgets the key."""
    storage = JsonObjectStorage()
    await storage.set('k', {'v': 1}, ttl=1)
    storage._expires_at['k'] = time.time() - 1  # noqa: SLF001

    assert await storage.get('k') is None
    assert await storage.snapshot() == {}


@pytest.mark.asyncio
async def test_snapshot_drops_expired_entries():
    """Snapshot skips keys whose deadline has passed and stops tracking them."""
    storage = JsonObjectStorage()
    await storage.set('alive', {'a': 1})
    await storage.set('dead', {'d': 1}, ttl=60)
    storage._expires_at['dead'] = time.time() - 1  # noqa: SLF001

    snapshot = await storage.snapshot()

    assert set(snapshot) == {'alive'}


@pytest.mark.asyncio
async def test_concurrent_writes_do_not_drop_keys():
    """Many concurrent set() calls all land in storage without losing entries."""
    storage = JsonObjectStorage()
    keys = [f'k{i}' for i in range(50)]

    await asyncio.gather(*(storage.set(key, {'i': key}) for key in keys))

    assert set(await storage.snapshot()) == set(keys)


@pytest.mark.asyncio
async def test_restore_rehydrates_remaining_lifetime():
    """An object snapshotted late in its life comes back with the time it had left."""
    storage = JsonObjectStorage()
    deadline = time.time() + 30

    stats = await storage.restore({'k': {'object': {'v': 1}, 'expires_at': deadline}})

    assert stats.restored == 1
    restored_deadline = (await storage.snapshot())['k']['expires_at']
    assert restored_deadline is not None
    # Allow a second of drift from the ceil() applied to the remaining seconds.
    assert abs(restored_deadline - deadline) <= 1


@pytest.mark.asyncio
async def test_restore_drops_already_expired_entries():
    """Entries whose deadline passed while the process was down are not resurrected."""
    storage = JsonObjectStorage()

    stats = await storage.restore({'gone': {'object': {'v': 1}, 'expires_at': time.time() - 1}})

    assert stats == (0, 1, 0)
    assert await storage.snapshot() == {}


@pytest.mark.parametrize(
    'entry',
    [
        pytest.param('not-a-dict', id='entry-not-a-mapping'),
        pytest.param({'expires_at': None}, id='object-missing'),
        pytest.param({'object': 'not-a-mapping', 'expires_at': None}, id='object-not-a-mapping'),
        pytest.param({'object': {'v': 1}, 'expires_at': 'soon'}, id='expiry-not-a-number'),
    ],
)
@pytest.mark.asyncio
async def test_restore_skips_malformed_entries(entry: object):
    """A structurally broken entry is counted and skipped, never raised on."""
    storage = JsonObjectStorage()

    stats = await storage.restore({'k': entry})

    assert stats.invalid == 1
    assert await storage.snapshot() == {}


@pytest.mark.asyncio
async def test_restore_rejects_a_non_mapping_snapshot():
    """A snapshot that is not a mapping at all is reported rather than crashing."""
    assert (await JsonObjectStorage().restore(['nope'])).invalid == 1


@pytest.mark.asyncio
async def test_clear_resets_state():
    """clear() drops both the cache and the expiry map."""
    storage = JsonObjectStorage()
    await storage.set('k', {'v': 1})

    await storage.clear()

    assert await storage.get('k') is None
    assert await storage.snapshot() == {}
