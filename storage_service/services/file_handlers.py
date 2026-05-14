from pathlib import Path

import aiofiles
import orjson
from structlog import getLogger

from storage_service.services.storage import storage
from storage_service.settings.core import OBJECTS_DATA

logger = getLogger(__name__)


async def save_objects_to_file() -> None:
    """Snapshot all live entries from RAM into a JSON file on disk."""
    logger.info('Save all objects from RAM to a file on disk')
    data = await storage.snapshot()
    if not data:
        logger.warning(
            'There are no objects in the storage. The contents of the storage will not be written to a file on disk',
        )
        return
    async with aiofiles.open(OBJECTS_DATA, 'w') as file:
        await file.write(orjson.dumps(data).decode())


async def restoring_objects_from_file() -> None:
    """
    Restore entries from disk into RAM and remove the snapshot file.

    The file is removed only after the restore loop has completed
    successfully, so a crash mid-restore does not lose data.
    """
    logger.info('Restore all objects from the file to RAM')
    path = Path(OBJECTS_DATA)
    try:
        async with aiofiles.open(path) as file:
            raw = await file.read()
    except FileNotFoundError:
        logger.warning('The file is not found on the disk. It is impossible to restore the storage state from a file')
        return

    try:
        data = orjson.loads(raw)
    except orjson.JSONDecodeError:
        logger.exception('Error when reading a file. It is impossible to restore the storage state from a file')
        return

    await storage.restore(data)
    path.unlink(missing_ok=True)
