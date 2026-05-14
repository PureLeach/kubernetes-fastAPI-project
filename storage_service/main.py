"""FastAPI application factory and uvicorn launcher."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI
from structlog import getLogger

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from storage_service.api.errors import register_error_handlers
from storage_service.api.middleware import RequestIdMiddleware
from storage_service.api.objects import objects_router
from storage_service.services.file_handlers import (
    restoring_objects_from_file,
    save_objects_to_file,
)
from storage_service.services.storage import JsonObjectStorage
from storage_service.services.storage import storage as default_storage
from storage_service.settings.core import Settings, get_settings
from storage_service.settings.log import setup_logging
from storage_service.settings.metrics import instrumentator
from storage_service.settings.probes import healthcheck_router

setup_logging()
logger = getLogger(__name__)

API_V1_PREFIX = '/v1'


def create_app(
    *,
    settings: Settings | None = None,
    storage: JsonObjectStorage | None = None,
) -> FastAPI:
    """
    Build a configured FastAPI application.

    Both `settings` and `storage` are injectable so tests can provide isolated
    instances. When omitted, the process-wide singletons are used.
    """
    settings = settings or get_settings()
    storage_instance = storage or default_storage

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await restoring_objects_from_file()
        yield
        await save_objects_to_file()

    app = FastAPI(
        title='JSON Object Storage',
        version='1.0.0',
        description='In-memory JSON object storage with TTL, persisted across restarts.',
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.storage = storage_instance

    app.add_middleware(RequestIdMiddleware)
    register_error_handlers(app)

    app.include_router(objects_router, prefix=API_V1_PREFIX)
    app.include_router(healthcheck_router, prefix='/probes')
    if settings.enable_metrics:
        instrumentator.instrument(app).expose(app)

    return app


app = create_app()


def start() -> None:
    settings = get_settings()
    logger.info('starting', host=settings.server_host, port=settings.server_port)
    uvicorn.run(
        'storage_service.main:app',
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
    )


if __name__ == '__main__':
    start()
