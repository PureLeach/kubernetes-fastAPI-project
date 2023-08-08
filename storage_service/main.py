import uvicorn
from fastapi import FastAPI
from structlog import getLogger

from storage_service.api.routers import objects_router
from storage_service.services.file_handlers import (
    restoring_objects_from_file,
    save_objects_to_file,
)
from storage_service.settings.core import (
    SERVER_HOST,
    SERVER_PORT,
    SERVER_RELOAD,
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
async def startup_event():
    """
    Функция отрабатывает перед запуском программы
    """
    await restoring_objects_from_file()


@app.on_event('shutdown')
async def shutdown_event():
    """
    Функция отрабатывает перед завершением программы
    """
    await save_objects_to_file()


def start():
    logger.info('Запуск приложения')
    uvicorn.run('storage_service.main:app', host=SERVER_HOST, port=SERVER_PORT, reload=SERVER_RELOAD)
    logger.info('Завершение работы приложения')


if __name__ == '__main__':
    start()
