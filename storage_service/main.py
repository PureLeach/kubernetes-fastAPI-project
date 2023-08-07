import uvicorn
from fastapi import FastAPI
from structlog import getLogger

from storage_service.api import endpoints
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
app.include_router(endpoints.router)
app.include_router(healthcheck_router, prefix="/probes")
instrumentator.instrument(app).expose(app)


def start():
    logger.info('Запуск приложения')
    uvicorn.run('storage_service.main:app', host=SERVER_HOST, port=SERVER_PORT, reload=SERVER_RELOAD)
    logger.info('Завершение работы приложения')


if __name__ == '__main__':
    start()
