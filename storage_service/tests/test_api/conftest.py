import pytest

from storage_service.settings.core import cache, cache_meta


@pytest.fixture()
async def create_objects_for_api():
    """Fixture for writing data to RAM"""

    key = 'test_api_object_key'
    object_data = {'test_object_two': 'payload'}
    expires = 50
    await cache.set(key, object_data, ttl=expires)
    cache_meta[key] = expires
    return key, object_data, expires
