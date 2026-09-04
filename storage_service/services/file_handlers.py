"""Reading and writing the on-disk snapshot of the object storage."""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

import aiofiles
import orjson
from structlog import getLogger

from storage_service.services.storage import SNAPSHOT_VERSION

if TYPE_CHECKING:
    from pathlib import Path

    from storage_service.services.storage import JsonObjectStorage

logger = getLogger(__name__)


async def save_snapshot(storage: JsonObjectStorage, path: Path) -> None:
    """
    Write every live entry to `path`, atomically.

    Writing via a temp file and `os.replace` means an interrupted write cannot
    leave a half-written snapshot. An empty storage still writes an empty
    snapshot; skipping the write would leave a stale file that resurrects
    deleted objects on the next start.
    """
    entries = await storage.snapshot()
    document = {'version': SNAPSHOT_VERSION, 'entries': entries}
    payload = orjson.dumps(document)

    await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
    tmp_path = path.with_name(f'{path.name}.tmp')
    async with aiofiles.open(tmp_path, 'wb') as file:
        await file.write(payload)
        await file.flush()
        await asyncio.to_thread(os.fsync, file.fileno())
    await asyncio.to_thread(os.replace, tmp_path, path)

    logger.info('snapshot_saved', path=str(path), keys=len(entries), bytes=len(payload))


async def restore_snapshot(storage: JsonObjectStorage, path: Path) -> None:
    """
    Load `path` into `storage` and remove it once the restore has succeeded.

    A missing snapshot is normal on first start. An unreadable one is kept on
    disk rather than discarded, so the failure stays diagnosable.
    """
    try:
        async with aiofiles.open(path, 'rb') as file:
            raw = await file.read()
    except FileNotFoundError:
        logger.info('snapshot_absent', path=str(path))
        return

    try:
        document = orjson.loads(raw)
    except orjson.JSONDecodeError:
        logger.exception('snapshot_parse_error', path=str(path))
        return

    if not isinstance(document, dict) or document.get('version') != SNAPSHOT_VERSION:
        logger.error(
            'snapshot_version_mismatch',
            path=str(path),
            expected=SNAPSHOT_VERSION,
            found=document.get('version') if isinstance(document, dict) else None,
        )
        return

    stats = await storage.restore(document.get('entries'))
    logger.info(
        'snapshot_restored',
        path=str(path),
        restored=stats.restored,
        expired=stats.expired,
        invalid=stats.invalid,
    )
    await asyncio.to_thread(path.unlink, missing_ok=True)
