import json
from pathlib import Path

import pytest
import pytest_asyncio

from storage_service.services.storage import storage
from storage_service.settings.core import get_settings


@pytest_asyncio.fixture()
async def create_objects():
    """Seed a known object into RAM."""
    key = 'test_object_key'
    object_data = {'test_object_one': 'payload'}
    expires = 100
    await storage.set(key, object_data, ttl=expires)
    return key, object_data, expires


@pytest.fixture()
def create_file():
    """Pre-write a snapshot file on disk for restore tests."""
    key = 'test_object_key'
    object_data = {'test_object_one': 'payload'}
    expires = 100

    file_content = {key: {'object': object_data, 'ttl': expires}}
    with Path(get_settings().objects_data_path).open('w') as file:
        json.dump(file_content, file)
    return key, object_data, expires


@pytest.fixture(autouse=True)
def cleanup_file():
    """Delete the snapshot file after each test if it exists."""
    yield
    path = Path(get_settings().objects_data_path)
    if path.exists():
        path.unlink()
