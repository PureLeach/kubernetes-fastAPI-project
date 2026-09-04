"""FastAPI application factory and uvicorn launcher."""

from __future__ import annotations

from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

import uvicorn
from fastapi import FastAPI
from structlog import getLogger

from storage_service.api.errors import register_error_handlers
from storage_service.api.middleware import BodySizeLimitMiddleware, RequestIdMiddleware
from storage_service.api.objects import objects_router
from storage_service.services.file_handlers import restore_snapshot, save_snapshot
from storage_service.services.storage import JsonObjectStorage
from storage_service.services.storage import storage as default_storage
from storage_service.settings.core import Settings, get_settings
from storage_service.settings.log import setup_logging
from storage_service.settings.metrics import instrumentator
from storage_service.settings.probes import build_healthcheck_router
from storage_service.tasks.scheduler import build_scheduler

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = getLogger(__name__)

API_V1_PREFIX = '/v1'


def _app_version() -> str:
    try:
        return version('kubernetes-fastapi-storage-service')
    except PackageNotFoundError:  # pragma: no cover
        return '0.0.0'


def create_app(
    *,
    settings: Settings | None = None,
    storage: JsonObjectStorage | None = None,
) -> FastAPI:
    """
    Build a configured FastAPI application.

    Both `settings` and `storage` are injectable so tests can provide isolated
    instances; omitted, the process-wide singletons are used. The lifespan,
    probes, scheduler and body-size limit all bind to *these* instances rather
    than to module-level globals, so two apps can coexist in one process.
    """
    settings = settings or get_settings()
    storage_instance = storage or default_storage
    setup_logging(settings.log_level_root)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await restore_snapshot(storage_instance, settings.objects_data_path)
        scheduler = build_scheduler(storage=storage_instance, settings=settings)
        if scheduler is not None:
            scheduler.start()
        try:
            yield
        finally:
            if scheduler is not None:
                scheduler.shutdown(wait=True)
            await save_snapshot(storage_instance, settings.objects_data_path)

    app = FastAPI(
        title='JSON Object Storage',
        version=_app_version(),
        description='In-memory JSON object storage with TTL, persisted across restarts.',
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.storage = storage_instance

    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_object_bytes)
    app.add_middleware(RequestIdMiddleware)
    register_error_handlers(app)

    app.include_router(objects_router, prefix=API_V1_PREFIX)
    app.include_router(build_healthcheck_router(settings.objects_data_path), prefix='/probes')
    if settings.enable_metrics:
        instrumentator.instrument(app).expose(app)

    return app


app = create_app()


def start() -> None:  # pragma: no cover
    settings = get_settings()
    logger.info('starting', host=settings.server_host, port=settings.server_port)
    uvicorn.run(
        'storage_service.main:app',
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
    )


if __name__ == '__main__':  # pragma: no cover
    start()
