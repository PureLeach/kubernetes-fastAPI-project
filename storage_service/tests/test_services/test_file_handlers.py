import json
from pathlib import Path

import pytest

from storage_service.services.file_handlers import (
    save_objects_to_file,
)
from storage_service.settings.core import OBJECTS_DATA


@pytest.mark.asyncio
async def test_save_objects_to_file(create_objects):
    """Проверяем, что создаётся файл с данными из ОЗУ"""

    await create_objects

    await save_objects_to_file()

    assert Path(OBJECTS_DATA).exists()


@pytest.mark.asyncio
async def test_checking_contents_of_the_file(create_objects):
    """Проверяем содержание файла"""

    key, value, expires = await create_objects

    await save_objects_to_file()
    with Path(OBJECTS_DATA).open('r') as file:
        object_data = json.load(file)

    assert object_data == {key: {'object': value, 'ttl': expires}}
