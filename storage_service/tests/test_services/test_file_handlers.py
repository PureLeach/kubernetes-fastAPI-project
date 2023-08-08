import json
from pathlib import Path

import pytest

from storage_service.services.file_handlers import (
    restoring_objects_from_file,
    save_objects_to_file,
)
from storage_service.settings.core import (
    OBJECTS_DATA,
    cache,
    cache_meta,
)


@pytest.mark.asyncio
async def test_save_objects_to_file(create_objects):
    """Проверяем, что создаётся файл с данными из ОЗУ"""

    await create_objects

    await save_objects_to_file()

    assert Path(OBJECTS_DATA).exists()


@pytest.mark.asyncio
async def test_checking_contents_of_the_file(create_objects):
    """Проверяем содержание файла"""

    key, object_data, expires = await create_objects

    await save_objects_to_file()
    with Path(OBJECTS_DATA).open('r') as file:
        json_data = json.load(file)

    assert json_data == {key: {'object': object_data, 'ttl': expires}}


@pytest.mark.asyncio
async def test_restoring_objects_from_file(create_file):
    """Проверяем, что данные из файла восстанавливаются в ОЗУ"""

    key, object_data, expires = await create_file

    await restoring_objects_from_file()
    object_in_ram_cache = await cache.get(key)

    assert cache_meta == {key: expires}
    assert object_in_ram_cache == object_data
