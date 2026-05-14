from pathlib import Path

import aiofiles
import orjson
from structlog import getLogger

from storage_service.services.storage import storage
from storage_service.settings.core import get_settings

logger = getLogger(__name__)


async def save_objects_to_file() -> None:
    """Snapshot all live entries from RAM into a JSON file on disk."""
    logger.info('saving_snapshot')
    data = await storage.snapshot()
    if not data:
        logger.warning('snapshot_skipped_empty_storage')
        return
    async with aiofiles.open(get_settings().objects_data_path, 'w') as file:
        await file.write(orjson.dumps(data).decode())


async def restoring_objects_from_file() -> None:
    """
    Restore entries from disk into RAM and remove the snapshot file.

    The file is removed only after the restore loop has completed
    successfully, so a crash mid-restore does not lose data.
    """
    logger.info('restoring_snapshot')
    path = Path(get_settings().objects_data_path)
    try:
        async with aiofiles.open(path) as file:
            raw = await file.read()
    except FileNotFoundError:
        logger.warning('snapshot_not_found', path=str(path))
        return

    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError:
        logger.exception('snapshot_parse_error', path=str(path))
        return

    await storage.restore(data)
    path.unlink(missing_ok=True)
