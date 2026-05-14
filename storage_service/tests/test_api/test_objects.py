import pytest
from fastapi import status

from storage_service.services.storage import storage


@pytest.mark.asyncio
async def test_set_object(client):
    """PUT /v1/objects/{key} stores the payload with the supplied TTL."""
    key = 'object_key'
    object_data = {'test_object_two': 'payload'}
    expires = 777

    response = client.put(f'/v1/objects/{key}', json=object_data, headers={'expires': str(expires)})

    assert response.status_code == status.HTTP_201_CREATED
    snapshot = await storage.snapshot()
    assert snapshot == {key: {'object': object_data, 'ttl': expires}}


@pytest.mark.asyncio
async def test_get_object(client, create_objects_for_api):
    """GET /v1/objects/{key} returns the object when present."""
    key, object_data, _ = create_objects_for_api

    response = client.get(f'/v1/objects/{key}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == object_data


@pytest.mark.asyncio
async def test_get_object_not_found(client):
    """GET /v1/objects/{key} returns the unified error envelope on 404."""
    response = client.get('/v1/objects/nonexistent')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert body['error']['code'] == 'not_found'
    assert body['error']['message'] == 'Object not found'
    assert body['error']['request_id']
