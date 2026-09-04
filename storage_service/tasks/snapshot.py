"""Background job that periodically flushes the storage to disk."""

from __future__ import annotations

from typing import TYPE_CHECKING

from structlog import getLogger

from storage_service.services.file_handlers import save_snapshot

if TYPE_CHECKING:
    from pathlib import Path

    from storage_service.services.storage import JsonObjectStorage

logger = getLogger(__name__)


async def periodic_snapshot(storage: JsonObjectStorage, path: Path) -> None:
    """
    Flush the storage to `path`, swallowing failures.

    Covers the hard stops the shutdown hook cannot — SIGKILL, OOM, a node going
    away. Must not raise: an exception escaping a job drops it from the schedule.
    """
    try:
        await save_snapshot(storage, path)
    except Exception:
        logger.exception('periodic_snapshot_failed', path=str(path))
