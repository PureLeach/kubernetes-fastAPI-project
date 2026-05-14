"""In-memory JSON object storage with optional per-key TTL."""

from __future__ import annotations

from typing import Any

from aiocache import Cache
from aiocache.serializers import JsonSerializer

JsonObject = dict[str, Any]
Snapshot = dict[str, dict[str, Any]]


class JsonObjectStorage:
    """
    Thin wrapper around aiocache that also tracks per-key TTLs.

    aiocache's in-memory backend exposes neither the live key set nor the
    TTLs of stored entries, so a parallel TTL map is unavoidable for
    snapshot/restore. This class is the single owner of that map — callers
    must not maintain their own.
    """

    def __init__(self) -> None:
        self._cache: Cache = Cache(Cache.MEMORY, serializer=JsonSerializer())
        self._ttls: dict[str, int | None] = {}

    async def set(self, key: str, value: JsonObject, ttl: int | None = None) -> None:
        await self._cache.set(key, value, ttl=ttl)
        self._ttls[key] = ttl

    async def get(self, key: str) -> JsonObject | None:
        value: JsonObject | None = await self._cache.get(key)
        if value is None:
            self._ttls.pop(key, None)
        return value

    async def snapshot(self) -> Snapshot:
        """Return all live entries together with their TTLs."""
        result: Snapshot = {}
        for key in list(self._ttls):
            value = await self._cache.get(key)
            if value is None:
                self._ttls.pop(key, None)
                continue
            result[key] = {'object': value, 'ttl': self._ttls[key]}
        return result

    async def restore(self, snapshot: Snapshot) -> None:
        for key, entry in snapshot.items():
            await self.set(key, entry['object'], ttl=entry.get('ttl'))

    async def clear(self) -> None:
        await self._cache.clear()
        self._ttls.clear()


storage = JsonObjectStorage()
