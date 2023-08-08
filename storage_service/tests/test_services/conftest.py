import json
from pathlib import Path

import pytest

from storage_service.settings.core import OBJECTS_DATA, cache, cache_meta


@pytest.fixture()
async def create_objects():
    """Фикстура для записи данных в ОЗУ"""

    key = 'test_object_key'
    object_data = {'test_object_one': 'payload'}
    expires = 100
    await cache.set(key, object_data, ttl=expires)
    cache_meta[key] = expires
    return key, object_data, expires


@pytest.fixture()
async def create_file():
    """Фикстура создания файла"""

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
    Удаление файла по завершении тестирования, если он существует
    Запускается после завершения каждого теста в рамках каталога
    """
    path = Path(OBJECTS_DATA)

    yield
    if path.exists():
        path.unlink()
