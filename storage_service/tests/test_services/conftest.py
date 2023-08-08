from pathlib import Path

import pytest

from storage_service.settings.core import OBJECTS_DATA, cache, cache_meta


@pytest.fixture()
async def create_objects():
    """Фикстура для записи данных в ОЗУ"""

    key = 'test_object_key'
    value = {'test_object_one': 'payload'}
    expires = 100
    await cache.set(key, value, ttl=expires)
    cache_meta[key] = expires
    return key, value, expires


@pytest.fixture(autouse=True)
def cleanup_file():
    """
    Удаление файла по завершении тестирования
    Запускается после завершения каждого теста в рамках каталога
    """

    yield
    Path(OBJECTS_DATA).unlink()  # Возвращаем путь к файлу как результат фикстуры
