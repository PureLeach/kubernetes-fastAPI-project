from structlog import getLogger

logger = getLogger(__name__)


async def trial_background_task():
    # Code for your background task goes here
    logger.info('Running background task...')
