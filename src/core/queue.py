from arq import create_pool, cron
from arq.connections import RedisSettings
from settings import settings

REDIS_HOST=settings.REDIS_HOST
REDIS_PORT=settings.REDIS_PORT
REDIS_DB=settings.REDIS_DB
OUTBOX_BACKOFF_POLL_DELAY=settings.OUTBOX_BACKOFF_POLL_DELAY

async def get_redis_pool():
    return await create_pool(RedisSettings(
            host=REDIS_HOST,
            port=REDIS_PORT,
            database=REDIS_DB,
        )
    )

class WorkerSettings:
    redis_settings = RedisSettings(
        host=REDIS_HOST,
        port=REDIS_PORT,
        database=REDIS_DB
    )
    on_startup = None
    on_shutdown = None

    functions = [
        "src.workers.notification_worker.consume_single_outbox",
        "src.workers.notification_worker.backfill_poll_outbox"
    ]

    cron_jobs = [
        cron(
            "src.workers.notification_worker.backfill_poll_outbox",
            second={0}
        )
    ]
    poll_delay = OUTBOX_BACKOFF_POLL_DELAY
