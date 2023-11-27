from pathlib import Path

import aiofiles
import orjson
from structlog import getLogger

from storage_service.settings.core import (
    OBJECTS_DATA,
    cache,
    cache_meta,
)

logger = getLogger(__name__)


async def save_objects_to_file():
    """
    Save data to disc in a json file.
    Data saving is done by retrieving all keys and ttl values from the cache_meta dictionary.
    """
    logger.info('Save all objects from RAM to a file on disc')
    data = {
        key: {'object': await cache.get(key), 'ttl': ttl} for key, ttl in cache_meta.items() if await cache.get(key)
    }
    if data:
        async with aiofiles.open(OBJECTS_DATA, 'w') as file:
            await file.write(orjson.dumps(data).decode())
    else:
        logger.warning(
            'There are no objects in the storage. The contents of the storage will not be written to a file on the disc',
        )


async def restoring_objects_from_file():
    """
    Restore data from the json file to RAM and delete it.
    """
    logger.info('Restore all objects from the file to RAM')
    try:
        async with aiofiles.open(OBJECTS_DATA, 'r') as file:
            object_data = orjson.loads(await file.read())
            for key, value in object_data.items():
                await cache.set(key, value.get('object'), ttl=value.get('ttl'))
                cache_meta[key] = value.get('ttl')
        Path(OBJECTS_DATA).unlink()
    except FileNotFoundError:
        logger.warning('The file is not found on the disc. It is impossible to restore the storage state from a file')
    except orjson.JSONDecodeError as e:
        logger.error(
            'Error when reading a file. It is impossible to restore the storage state from a file',
            error=e,
        )
