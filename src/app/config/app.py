import logging
import sys
from functools import lru_cache
from typing import cast

import structlog
from httpx_oauth.clients.github import GitHubOAuth2
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.logging.config import (
    LoggingConfig,
    StructLoggingConfig,
    default_logger_factory,
    default_structlog_processors,
    default_structlog_standard_lib_processors,
)
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.plugins.problem_details import ProblemDetailsConfig
from litestar.plugins.sqlalchemy import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from litestar.plugins.structlog import StructlogConfig
from litestar.template import TemplateConfig
from litestar_saq import CronJob, QueueConfig, SAQConfig
from litestar_vite import ViteConfig

from .base import get_settings

settings = get_settings()

compression = CompressionConfig(backend="gzip")
csrf = CSRFConfig(
    secret=settings.app.SECRET_KEY,
    cookie_secure=settings.app.CSRF_COOKIE_SECURE,
    cookie_name=settings.app.CSRF_COOKIE_NAME,
)
cors = CORSConfig(allow_origins=cast("list[str]", settings.app.ALLOWED_CORS_ORIGINS))
alchemy = SQLAlchemyAsyncConfig(
    engine_instance=settings.db.get_engine(),
    before_send_handler="autocommit",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicAsyncConfig(
        version_table_name=settings.db.MIGRATION_DDL_VERSION_TABLE,
        script_config=settings.db.MIGRATION_CONFIG,
        script_location=settings.db.MIGRATION_PATH,
    ),
)
templates = TemplateConfig(engine=JinjaTemplateEngine(directory=settings.vite.TEMPLATE_DIR))
problem_details = ProblemDetailsConfig(enable_for_all_http_exceptions=True)
vite = ViteConfig(
    bundle_dir=settings.vite.BUNDLE_DIR,
    resource_dir=settings.vite.RESOURCE_DIR,
    use_server_lifespan=settings.vite.USE_SERVER_LIFESPAN,
    dev_mode=settings.vite.DEV_MODE,
    hot_reload=settings.vite.HOT_RELOAD,
    is_react=settings.vite.ENABLE_REACT_HELPERS,
    port=settings.vite.PORT,
    host=settings.vite.HOST,
)
github_oauth = GitHubOAuth2(
    client_id=settings.app.GITHUB_OAUTH2_CLIENT_ID,
    client_secret=settings.app.GITHUB_OAUTH2_CLIENT_SECRET,
)

saq = SAQConfig(
    dsn=settings.redis.URL,
    web_enabled=settings.saq.WEB_ENABLED,
    worker_processes=settings.saq.PROCESSES,
    use_server_lifespan=settings.saq.USE_SERVER_LIFESPAN,
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


@lru_cache
def _is_tty() -> bool:
    return bool(sys.stderr.isatty() or sys.stdout.isatty())


_render_as_json = not _is_tty()
_structlog_default_processors = default_structlog_processors(as_json=_render_as_json)
_structlog_default_processors.insert(1, structlog.processors.EventRenamer("message"))
_structlog_standard_lib_processors = default_structlog_standard_lib_processors(as_json=_render_as_json)
_structlog_standard_lib_processors.insert(1, structlog.processors.EventRenamer("message"))

log = StructlogConfig(
    structlog_logging_config=StructLoggingConfig(
        log_exceptions="always",
        processors=_structlog_default_processors,
        logger_factory=default_logger_factory(as_json=_render_as_json),
        standard_lib_logging_config=LoggingConfig(
            root={"level": logging.getLevelName(settings.log.LEVEL), "handlers": ["queue_listener"]},
            formatters={
                "standard": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": _structlog_standard_lib_processors,
                },
            },
            loggers={
                "granian.access": {
                    "propagate": False,
                    "level": settings.log.GRANIAN_ACCESS_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "granian.error": {
                    "propagate": False,
                    "level": settings.log.GRANIAN_ERROR_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "saq": {
                    "propagate": False,
                    "level": settings.log.SAQ_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "sqlalchemy.engine": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "sqlalchemy.pool": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
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
