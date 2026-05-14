import pytest_asyncio

from storage_service.services.storage import storage


@pytest_asyncio.fixture()
async def create_objects_for_api():
    """Seed a known object into RAM and yield its identifiers."""
    key = 'test_api_object_key'
    object_data = {'test_object_two': 'payload'}
    expires = 50
    await storage.set(key, object_data, ttl=expires)
    return key, object_data, expires
