"""In-memory JSON object storage with optional per-key TTL."""

from __future__ import annotations

import math
import time
from typing import Any, NamedTuple, TypedDict, TypeGuard

from aiocache import Cache
from aiocache.serializers import JsonSerializer

JsonObject = dict[str, Any]

SNAPSHOT_VERSION = 1


class SnapshotEntry(TypedDict):
    """A stored object and the instant it expires at."""

    object: JsonObject
    expires_at: float | None


Snapshot = dict[str, SnapshotEntry]


class RestoreStats(NamedTuple):
    """Outcome of a restore: how many entries were loaded, dropped, skipped."""

    restored: int
    expired: int
    invalid: int


def _is_valid_entry(entry: object) -> TypeGuard[SnapshotEntry]:
    if not isinstance(entry, dict):
        return False
    if not isinstance(entry.get('object'), dict):
        return False
    expires_at = entry.get('expires_at')
    return expires_at is None or isinstance(expires_at, int | float)


class JsonObjectStorage:
    """
    Thin wrapper around aiocache that also tracks per-key expiry.

    aiocache's in-memory backend exposes neither the live key set nor the
    TTLs of stored entries, so a parallel expiry map is unavoidable for
    snapshot/restore. This class is the single owner of that map — callers
    must not maintain their own.

    Expiry is kept as an absolute timestamp, not the original TTL, so a
    restored object keeps the lifetime it had left rather than a fresh one.
    """

    def __init__(self) -> None:
        self._cache: Cache = Cache(Cache.MEMORY, serializer=JsonSerializer())
        self._expires_at: dict[str, float | None] = {}

    async def set(self, key: str, value: JsonObject, ttl: int | None = None) -> None:
        """Store `value` under `key`, expiring it after `ttl` seconds if given."""
        await self._cache.set(key, value, ttl=ttl)
        self._expires_at[key] = time.time() + ttl if ttl is not None else None

    def _is_expired(self, key: str, now: float) -> bool:
        expires_at = self._expires_at.get(key)
        return expires_at is not None and expires_at <= now

    async def get(self, key: str) -> JsonObject | None:
        """Return the object stored under `key`, or `None` if missing/expired."""
        if self._is_expired(key, time.time()):
            await self._forget(key)
            return None
        value: JsonObject | None = await self._cache.get(key)
        if value is None:
            self._expires_at.pop(key, None)
        return value

    async def _forget(self, key: str) -> None:
        await self._cache.delete(key)
        self._expires_at.pop(key, None)

    async def snapshot(self) -> Snapshot:
        """Return all live entries together with their absolute expiry."""
        now = time.time()
        result: Snapshot = {}
        for key in list(self._expires_at):
            if self._is_expired(key, now):
                await self._forget(key)
                continue
            value = await self._cache.get(key)
            if value is None:
                self._expires_at.pop(key, None)
                continue
            result[key] = {'object': value, 'expires_at': self._expires_at[key]}
        return result

    async def restore(self, snapshot: object) -> RestoreStats:
        """
        Load `snapshot` back into the cache with the remaining lifetimes.

        Malformed entries are skipped, not raised on — a broken snapshot must
        not restart-loop the pod. Already-expired entries are dropped.
        """
        if not isinstance(snapshot, dict):
            return RestoreStats(restored=0, expired=0, invalid=1)

        now = time.time()
        restored = expired = invalid = 0
        for key, entry in snapshot.items():
            if not isinstance(key, str) or not _is_valid_entry(entry):
                invalid += 1
                continue

            expires_at = entry['expires_at']
            ttl: int | None = None
            if expires_at is not None:
                remaining = expires_at - now
                if remaining <= 0:
                    expired += 1
                    continue
                ttl = math.ceil(remaining)

            await self.set(key, entry['object'], ttl=ttl)
            restored += 1

        return RestoreStats(restored=restored, expired=expired, invalid=invalid)

    async def clear(self) -> None:
        """Drop every entry and its expiry metadata."""
        await self._cache.clear()
        self._expires_at.clear()


storage = JsonObjectStorage()
