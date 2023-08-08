import json
from pathlib import Path

import pytest

from storage_service.settings.core import OBJECTS_DATA, cache, cache_meta


@pytest.fixture()
async def create_objects():
    """Fixture for writing data to RAM"""

    key = 'test_object_key'
    object_data = {'test_object_one': 'payload'}
    expires = 100
    await cache.set(key, object_data, ttl=expires)
    cache_meta[key] = expires
    return key, object_data, expires


@pytest.fixture()
async def create_file():
    """File creation fixture"""

    key = 'test_object_key'
    object_data = {'test_object_one': 'payload'}
    expires = 100

    file_content = {key: {'object': object_data, 'ttl': expires}}
    with Path(OBJECTS_DATA).open('w') as file:
        json.dump(file_content, file)
    return key, object_data, expires


@pytest.fixture(autouse=True)
def cleanup_file():
    """
    Deleting a file at the end of testing, if it exists.
    Runs after completion of each test within the catalogue
    """
    path = Path(OBJECTS_DATA)

    yield
    if path.exists():
        path.unlink()
