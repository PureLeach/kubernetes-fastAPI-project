import json
from pathlib import Path

import pytest

from storage_service.services.file_handlers import (
    restoring_objects_from_file,
    save_objects_to_file,
)
from storage_service.services.storage import storage
from storage_service.settings.core import OBJECTS_DATA


@pytest.mark.asyncio
async def test_save_objects_to_file(create_objects):
    """save_objects_to_file writes the snapshot file when storage is non-empty."""
    await save_objects_to_file()

    assert Path(OBJECTS_DATA).exists()


@pytest.mark.asyncio
async def test_checking_contents_of_the_file(create_objects):
    """The snapshot file contains every live entry plus its TTL."""
    key, object_data, expires = create_objects

    await save_objects_to_file()
    with Path(OBJECTS_DATA).open() as file:
        json_data = json.load(file)

    assert json_data == {key: {'object': object_data, 'ttl': expires}}


@pytest.mark.asyncio
async def test_restoring_objects_from_file(create_file):
    """restoring_objects_from_file repopulates RAM and removes the snapshot file."""
    key, object_data, expires = create_file

    await restoring_objects_from_file()

    snapshot = await storage.snapshot()
    assert snapshot == {key: {'object': object_data, 'ttl': expires}}
    assert not Path(OBJECTS_DATA).exists()
