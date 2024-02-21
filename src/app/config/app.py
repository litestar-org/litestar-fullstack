import logging
from typing import cast

from advanced_alchemy import AsyncSessionConfig
from advanced_alchemy.config import AlembicAsyncConfig
from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.logging.config import LoggingConfig, StructLoggingConfig
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.plugins.structlog import StructlogConfig
from litestar_saq import CronJob, QueueConfig, SAQConfig
from litestar_vite import ViteConfig

from .base import get_settings

_settings = get_settings()

compression = CompressionConfig(backend="gzip")
csrf = CSRFConfig(
    secret=_settings.app.SECRET_KEY,
    cookie_secure=_settings.app.CSRF_COOKIE_SECURE,
    cookie_name=_settings.app.CSRF_COOKIE_NAME,
)
cors = CORSConfig(allow_origins=cast("list[str]", _settings.app.ALLOWED_CORS_ORIGINS))
alchemy = SQLAlchemyAsyncConfig(
    connection_string=_settings.db.URL,
    before_send_handler=autocommit_before_send_handler,
    session_config=AsyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicAsyncConfig(
        version_table_name=_settings.db.MIGRATION_DDL_VERSION_TABLE,
        script_config=_settings.db.MIGRATION_CONFIG,
        script_location=_settings.db.MIGRATION_PATH,
    ),
)
vite = ViteConfig(
    bundle_dir=_settings.vite.BUNDLE_DIR,
    resource_dir=_settings.vite.RESOURCE_DIR,
    template_dir=_settings.vite.TEMPLATE_DIR,
    use_server_lifespan=_settings.vite.USE_SERVER_LIFESPAN,
    dev_mode=_settings.vite.DEV_MODE,
    hot_reload=_settings.vite.HOT_RELOAD,
    is_react=_settings.vite.ENABLE_REACT_HELPERS,
    port=_settings.vite.PORT,
    host=_settings.vite.HOST,
)
saq = SAQConfig(
    redis=_settings.redis.client,
    web_enabled=_settings.saq.WEB_ENABLED,
    worker_processes=_settings.saq.PROCESSES,
    use_server_lifespan=_settings.saq.USE_SERVER_LIFESPAN,
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
)

log = StructlogConfig(
    structlog_logging_config=StructLoggingConfig(
        log_exceptions="always",
        traceback_line_limit=4,
        standard_lib_logging_config=LoggingConfig(
            root={"level": logging.getLevelName(_settings.log.LEVEL), "handlers": ["queue_listener"]},
            loggers={
                "uvicorn.access": {
                    "propagate": False,
                    "level": _settings.log.UVICORN_ACCESS_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "uvicorn.error": {
                    "propagate": False,
                    "level": _settings.log.UVICORN_ERROR_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "granian.access": {
                    "propagate": False,
                    "level": _settings.log.GRANIAN_ACCESS_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "granian.error": {
                    "propagate": False,
                    "level": _settings.log.GRANIAN_ERROR_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "saq": {
                    "propagate": False,
                    "level": _settings.log.SAQ_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "sqlalchemy.engine": {
                    "propagate": False,
                    "level": _settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "sqlalchemy.pool": {
                    "propagate": False,
                    "level": _settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
            },
        ),
    ),
    middleware_logging_config=LoggingMiddlewareConfig(
        request_log_fields=["method", "path", "path_params", "query"],
        response_log_fields=["status_code"],
    ),
)
