import json
from pathlib import Path

import pytest

from storage_service.services.file_handlers import (
    restoring_objects_from_file,
    save_objects_to_file,
)
from storage_service.services.storage import storage
from storage_service.settings.core import get_settings


@pytest.mark.asyncio
async def test_save_objects_to_file(create_objects):
    """save_objects_to_file writes the snapshot file when storage is non-empty."""
    await save_objects_to_file()

    assert Path(get_settings().objects_data_path).exists()


@pytest.mark.asyncio
async def test_checking_contents_of_the_file(create_objects):
    """The snapshot file contains every live entry plus its TTL."""
    key, object_data, expires = create_objects

    await save_objects_to_file()
    with Path(get_settings().objects_data_path).open() as file:
        json_data = json.load(file)

    assert json_data == {key: {'object': object_data, 'ttl': expires}}


@pytest.mark.asyncio
async def test_restoring_objects_from_file(create_file):
    """restoring_objects_from_file repopulates RAM and removes the snapshot file."""
    key, object_data, expires = create_file

    await restoring_objects_from_file()

    snapshot = await storage.snapshot()
    assert snapshot == {key: {'object': object_data, 'ttl': expires}}
    assert not Path(get_settings().objects_data_path).exists()


@pytest.mark.asyncio
async def test_restore_from_corrupted_file_keeps_file_and_storage_empty():
    """A non-JSON snapshot file must not crash startup; it is left in place for inspection."""
    path = Path(get_settings().objects_data_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('this is not json {{{')

    await restoring_objects_from_file()

    assert path.exists(), 'Corrupted file must be preserved for retry / debugging'
    assert await storage.snapshot() == {}


@pytest.mark.asyncio
async def test_restore_when_file_missing_is_a_no_op():
    """restoring_objects_from_file silently no-ops when there is no snapshot file."""
    path = Path(get_settings().objects_data_path)
    if path.exists():
        path.unlink()

    await restoring_objects_from_file()

    assert await storage.snapshot() == {}


@pytest.mark.asyncio
async def test_save_when_storage_empty_does_not_create_file():
    """An empty storage produces no snapshot file (avoids overwriting prior good state with `{}`)."""
    path = Path(get_settings().objects_data_path)
    if path.exists():
        path.unlink()

    await save_objects_to_file()

    assert not path.exists()
