import asyncio

from structlog import getLogger

from storage_service.settings.scheduler import scheduler

logger = getLogger(__name__)


async def start_scheduler():
    logger.info('Starting the task scheduler')
    scheduler.start()


async def stop_scheduler():
    logger.info('Shutting down the task scheduler')
    scheduler.shutdown()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_scheduler())
    try:
        loop.run_forever()
    finally:
        asyncio.run(stop_scheduler())
