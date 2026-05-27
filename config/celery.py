from celery import Celery
from celery.schedules import crontab
import asyncio
from os import environ

from app.worker.core.handler import WorkerHandler
import config.enviroment as env
from config.settings.base import connect_db
import time

redis_uri = f"redis://{env.REDIS['HOST']}"

celery_app = Celery(
    'config',
    broker=redis_uri + "/0",
    backend=redis_uri + "/1",
    include=[]
)

environ['TZ'] = env.ENVIRONMENT['TIMEZONE']
time.tzset()

celery_app.conf.timezone = environ.get('TIMEZONE')
celery_app.conf.enable_utc = True


async def task_init():
    is_test = env.ENVIRONMENT['APP_ENV'] not in ['production', 'qa', 'staging']
    await connect_db(is_test=is_test)


async def run_with_db(coro):
    is_test = env.ENVIRONMENT['APP_ENV'] not in ['production', 'qa', 'staging']
    await connect_db(is_test=is_test)
    return await coro


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute=0, hour='*'),
        enqueue_document_not_processed.s(),
        name='enqueue every hour the not processed task'
    )


@celery_app.task
def enqueue_document_not_processed():
    asyncio.run(run_with_db(WorkerHandler.enqueue_document_not_processed()))


@celery_app.task
def document_request(**kwargs):
    asyncio.run(run_with_db(WorkerHandler.request_task(**kwargs)))
