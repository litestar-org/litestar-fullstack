import os

from litestar.contrib.pydantic import PydanticPlugin
from litestar_aiosql import AiosqlConfig, AiosqlPlugin
from litestar_saq import CronJob, QueueConfig, SAQConfig, SAQPlugin
from litestar_vite import ViteConfig, VitePlugin

from app.lib import settings

pydantic = PydanticPlugin(prefer_alias=True)
aiosql = AiosqlPlugin(config=AiosqlConfig())
vite = VitePlugin(
    config=ViteConfig(
        bundle_dir=settings.BUNDLE_DIR,
        resource_dir=settings.RESOURCE_DIR,
        template_dir=settings.TEMPLATES_DIR,
        dev_mode=settings.app.DEV_MODE,
        hot_reload=os.environ.get("VITE_HOT_RELOAD", None) not in {None, "no", "false", "False", "0"},
        use_server_lifespan=True,
        port=int(os.environ.get("VITE_PORT", 3006)),
        host=os.environ.get("VITE_HOST", "localhost"),
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
                tasks=["app.domain.system.tasks.system_task", "app.domain.system.tasks.system_upkeep"],
                scheduled_tasks=[
                    CronJob(
                        function="app.domain.system.tasks.system_upkeep",
                        unique=True,
                        cron="0 * * * *",
                        timeout=500,
                    ),
                ],
            ),
            QueueConfig(
                name="background-tasks",
                tasks=["app.domain.system.tasks.background_worker_task"],
                scheduled_tasks=[
                    CronJob(
                        function="app.domain.system.tasks.background_worker_task",
                        unique=True,
                        cron="* * * * *",
                        timeout=300,
                    ),
                ],
            ),
        ],
    ),
)
