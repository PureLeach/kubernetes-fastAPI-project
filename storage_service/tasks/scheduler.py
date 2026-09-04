"""APScheduler wiring for the application's background jobs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from structlog import getLogger

from storage_service.tasks.snapshot import periodic_snapshot

if TYPE_CHECKING:
    from storage_service.services.storage import JsonObjectStorage
    from storage_service.settings.core import Settings

logger = getLogger(__name__)

SNAPSHOT_JOB_ID = 'periodic_snapshot'


def build_scheduler(*, storage: JsonObjectStorage, settings: Settings) -> AsyncIOScheduler | None:
    """
    Return a scheduler wired to `storage`, or `None` when jobs are disabled.

    Runs on the API's own event loop: the job snapshots in-memory storage, which
    a separate process could not reach. Built per application, not at import
    time, so each app gets a scheduler bound to its own storage.
    """
    if settings.snapshot_interval_seconds <= 0:
        logger.info('scheduler_disabled')
        return None

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        periodic_snapshot,
        trigger='interval',
        seconds=settings.snapshot_interval_seconds,
        id=SNAPSHOT_JOB_ID,
        kwargs={'storage': storage, 'path': settings.objects_data_path},
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    return scheduler
