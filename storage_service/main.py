import uvicorn
from fastapi import FastAPI
from structlog import getLogger

from storage_service.api import endpoints
from storage_service.core.log import setup_logging
from storage_service.core.metrics import instrumentator
from storage_service.core.settings import (
    SERVER_HOST,
    SERVER_PORT,
    SERVER_RELOAD,
)

setup_logging()
logger = getLogger(__name__)

app = FastAPI()
app.include_router(endpoints.router)

instrumentator.instrument(app).expose(app)


def start():
    logger.info('Запуск приложения')
    uvicorn.run('storage_service.main:app', host=SERVER_HOST, port=SERVER_PORT, reload=SERVER_RELOAD)
    logger.info('Завершение работы приложения')


if __name__ == '__main__':
    start()
