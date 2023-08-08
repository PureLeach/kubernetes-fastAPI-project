import pytest
from fastapi import status

from storage_service.settings.core import cache, cache_meta


@pytest.mark.asyncio
async def test_set_object(client):
    """Проверка запроса PUT /objects/{key}"""

    key = 'object_key'
    object_data = {'test_object_two': 'payload'}
    expires = 777

    response = client.put(f'/objects/{key}', json=object_data, headers={'expires': str(expires)})
    object_in_ram_cache = await cache.get(key)

    assert response.status_code == status.HTTP_201_CREATED
    assert object_in_ram_cache == object_data
    assert cache_meta == {key: expires}


@pytest.mark.asyncio
async def test_get_object(client, create_objects_for_api):
    """Проверка запроса PUT /objects/{key}. Кейс: объект существует в ОЗУ"""

    key, object_data, expires = await create_objects_for_api

    response = client.get(f'/objects/{key}')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == object_data


@pytest.mark.asyncio
async def test_get_object_not_found(client):
    """Проверка запроса PUT /objects/{key}. Кейс: объект НЕ существует в ОЗУ"""

    key = 'nonexistent'

    response = client.get(f'/objects/{key}')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Объект не найден'}
