from litestar_aiosql import AiosqlConfig, AiosqlPlugin
from litestar_saq import CronJob, QueueConfig, SAQConfig, SAQPlugin
from litestar_vite import ViteConfig, VitePlugin

from app.domain.system import tasks
from app.lib import settings

aiosql = AiosqlPlugin(config=AiosqlConfig())
vite = VitePlugin(
    config=ViteConfig(
        static_dir=settings.STATIC_DIR,
        templates_dir=settings.TEMPLATES_DIR,
        hot_reload=settings.app.DEV_MODE,
        port=3005,
    ),
)
saq = SAQPlugin(
    config=SAQConfig(
        redis_url=settings.redis.URL,
        web_enabled=True,
        worker_processes=1,
        queue_configs=[
            QueueConfig(
                name="system-tasks",
                tasks=[tasks.system_task, tasks.system_upkeep],
                scheduled_tasks=[CronJob(function=tasks.system_upkeep, unique=True, cron="0 * * * *", timeout=500)],
            ),
            QueueConfig(
                name="background-tasks",
                tasks=[tasks.background_worker_task],
                scheduled_tasks=[
                    CronJob(function=tasks.background_worker_task, unique=True, cron="* * * * *", timeout=300),
                ],
            ),
        ],
    ),
)
