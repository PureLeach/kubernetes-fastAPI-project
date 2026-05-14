import pytest
from fastapi import status

from storage_service.services.storage import storage


@pytest.mark.asyncio
async def test_set_object(client):
    """PUT /objects/{key} stores the payload with the supplied TTL."""
    key = 'object_key'
    object_data = {'test_object_two': 'payload'}
    expires = 777

    response = client.put(f'/objects/{key}', json=object_data, headers={'expires': str(expires)})

    assert response.status_code == status.HTTP_201_CREATED
    snapshot = await storage.snapshot()
    assert snapshot == {key: {'object': object_data, 'ttl': expires}}


@pytest.mark.asyncio
async def test_get_object(client, create_objects_for_api):
    """GET /objects/{key} returns the object when present."""
    key, object_data, _ = create_objects_for_api

    response = client.get(f'/objects/{key}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == object_data


@pytest.mark.asyncio
async def test_get_object_not_found(client):
    """GET /objects/{key} returns 404 when the key is missing."""
    response = client.get('/objects/nonexistent')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Object not found'}
