import json
from pathlib import Path

from structlog import getLogger

from storage_service.settings.core import (
    OBJECTS_DATA,
    cache,
    cache_meta,
)

logger = getLogger(__name__)


async def save_objects_to_file():
    """
    Сохраняем данные на диск в json-файл.
    Сохранение данных происходит путём получения всех ключей и значений ttl из словаря cache_meta.
    """
    logger.info('Сохраняем все объекты из оперативной памяти в файл на диске')
    data = {
        key: {'object': await cache.get(key), 'ttl': ttl} for key, ttl in cache_meta.items() if await cache.get(key)
    }
    if data:
        with Path(OBJECTS_DATA).open('w') as file:
            json.dump(data, file)
    else:
        logger.warning('В памяти нет объектов. Запись содержимого хранилища в файл на диске не будет произведена')


async def restoring_objects_from_file():
    """
    Восстанавливаем данные из json-файла в оперативную память и удаляем его.
    """
    logger.info('Восстанавливаем все объекты из файла в оперативную память')
    try:
        with Path(OBJECTS_DATA).open('r') as file:
            object_data = json.load(file)
            for key, value in object_data.items():
                await cache.set(key, value.get('object'), ttl=value.get('ttl'))
                cache_meta[key] = value.get('ttl')
        Path(OBJECTS_DATA).unlink()
    except FileNotFoundError:
        logger.warning('Файл не найден на диске. Восстановление состояния хранилища из файла невозможно осуществить')
    except json.decoder.JSONDecodeError as e:
        logger.error(
            'Ошибка при прочтении файла. Восстановление состояния хранилища из файла невозможно осуществить',
            error=e,
        )
