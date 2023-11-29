from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from storage_service.tasks.background_task import trial_background_task

scheduler = AsyncIOScheduler()
scheduler.add_job(trial_background_task, 'interval', seconds=10)
scheduler.add_job(trial_background_task, CronTrigger.from_crontab('10 15 * * *'))
