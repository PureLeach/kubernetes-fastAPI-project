from structlog import getLogger

logger = getLogger(__name__)


async def trial_background_task():
    logger.info('trial_task_fired')
