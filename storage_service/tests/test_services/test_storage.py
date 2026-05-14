from __future__ import annotations

import asyncio

import pytest

from storage_service.services.storage import JsonObjectStorage


@pytest.mark.asyncio
async def test_get_returns_none_after_ttl_expiry():
    """Reading a key past its TTL returns None and clears the parallel TTL map."""
    s = JsonObjectStorage()
    await s.set('k', {'v': 1}, ttl=1)
    await asyncio.sleep(1.2)
    assert await s.get('k') is None
    assert 'k' not in s._ttls  # noqa: SLF001 — verifying no leak


@pytest.mark.asyncio
async def test_snapshot_drops_expired_entries():
    """Snapshot skips keys whose TTL has expired and stops tracking them."""
    s = JsonObjectStorage()
    await s.set('alive', {'a': 1}, ttl=None)
    await s.set('dead', {'d': 1}, ttl=1)
    await asyncio.sleep(1.2)
    snap = await s.snapshot()
    assert 'alive' in snap
    assert 'dead' not in snap


@pytest.mark.asyncio
async def test_concurrent_writes_do_not_drop_keys():
    """Many concurrent set() calls all land in storage without losing entries."""
    s = JsonObjectStorage()
    keys = [f'k{i}' for i in range(50)]
    await asyncio.gather(*(s.set(k, {'i': k}, ttl=None) for k in keys))
    snap = await s.snapshot()
    assert set(snap.keys()) == set(keys)


@pytest.mark.asyncio
async def test_restore_repopulates_storage():
    """restore() rehydrates both values and TTLs from a snapshot dict."""
    s = JsonObjectStorage()
    payload = {'k1': {'object': {'v': 1}, 'ttl': None}, 'k2': {'object': {'v': 2}, 'ttl': 100}}
    await s.restore(payload)
    snap = await s.snapshot()
    assert snap == payload


@pytest.mark.asyncio
async def test_clear_resets_state():
    """clear() drops both the cache and the TTL map."""
    s = JsonObjectStorage()
    await s.set('k', {'v': 1})
    await s.clear()
    assert await s.get('k') is None
    assert s._ttls == {}  # noqa: SLF001
