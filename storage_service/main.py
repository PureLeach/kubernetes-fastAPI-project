import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from structlog import getLogger

from storage_service.api.routers import objects_router
from storage_service.settings.core import (
    OBJECTS_DATA,
    SERVER_HOST,
    SERVER_PORT,
    SERVER_RELOAD,
    cache,
    cache_keys,
)
from storage_service.settings.log import setup_logging
from storage_service.settings.metrics import instrumentator
from storage_service.settings.probes import healthcheck_router

setup_logging()
logger = getLogger(__name__)

app = FastAPI()
app.include_router(objects_router)
app.include_router(healthcheck_router, prefix='/probes')
instrumentator.instrument(app).expose(app)


@app.on_event('startup')
async def restoring_objects_from_file():
    """
    Функция отрабатывает перед запуском программы
    """
    logger.info('Восстанавливаем все объекты из файла в оперативную память')
    try:
        with Path(OBJECTS_DATA).open('r') as file:
            object_data = json.load(file)
            cache_keys.update(object_data.keys())
            await cache.multi_set(object_data.items())
        Path(OBJECTS_DATA).unlink()
    except FileNotFoundError:
        logger.warning('Файл не найден на диске. Восстановление состояния хранилища из файла невозможно осуществить')
    except json.decoder.JSONDecodeError as e:
        logger.error(
            'Ошибка при прочтении файла. Восстановление состояния хранилища из файла невозможно осуществить',
            error=e,
        )


@app.on_event('shutdown')
async def save_objects_to_file():
    """
    Функция отрабатывает перед завершением программы
    """
    logger.info('Сохраняем все объекты из оперативной памяти в файл на диске')

    data = {}
    for key in cache_keys:
        object_data = await cache.get(key)
        if object_data:
            data[key] = object_data
    if data:
        with Path(OBJECTS_DATA).open('w') as file:
            json.dump(data, file)
    else:
        logger.warning('В памяти нет объектов. Запись содержимого хранилища в файл на диске не будет произведена')


def start():
    logger.info('Запуск приложения')
    uvicorn.run('storage_service.main:app', host=SERVER_HOST, port=SERVER_PORT, reload=SERVER_RELOAD)
    logger.info('Завершение работы приложения')


if __name__ == '__main__':
    start()
