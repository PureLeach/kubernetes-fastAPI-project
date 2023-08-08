import uvicorn
from fastapi import FastAPI
from structlog import getLogger

from storage_service.api.routers import objects_router
from storage_service.settings.core import (
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


@app.on_event('shutdown')
async def save_objects_to_file():
    """
    Функция отрабатывает перед завершением программы
    """
    logger.info('Сохраняем все объекты из оперативной памяти в файл на диске')
    result = await cache.multi_get(cache_keys)
    if result:
        pass
    else:
        logger.info('В памяти нет объектов. Запись содержимого хранилища в файл на диске не будет произведена')


def start():
    logger.info('Запуск приложения')
    uvicorn.run('storage_service.main:app', host=SERVER_HOST, port=SERVER_PORT, reload=SERVER_RELOAD)
    logger.info('Завершение работы приложения')


if __name__ == '__main__':
    start()
