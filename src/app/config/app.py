import logging
import sys
from functools import lru_cache
from typing import cast

import logfire
import structlog
from advanced_alchemy.extensions.litestar import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    async_autocommit_handler_maker,
)
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.logging.config import (
    LoggingConfig,
    StructLoggingConfig,
    default_logger_factory,
    default_structlog_processors,
    default_structlog_standard_lib_processors,
)
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.plugins.structlog import StructlogConfig
from litestar_saq import CronJob, QueueConfig, SAQConfig
from litestar_vite import ViteConfig
from litestar_vite.inertia import InertiaConfig

from .base import get_settings

settings = get_settings()


compression = CompressionConfig(backend="gzip")
csrf = CSRFConfig(
    secret=settings.app.SECRET_KEY,
    cookie_secure=settings.app.CSRF_COOKIE_SECURE,
    cookie_name=settings.app.CSRF_COOKIE_NAME,
    header_name=settings.app.CSRF_HEADER_NAME,
)
cors = CORSConfig(allow_origins=cast("list[str]", settings.app.ALLOWED_CORS_ORIGINS))


alchemy = SQLAlchemyAsyncConfig(
    engine_instance=settings.db.get_engine(),
    before_send_handler=async_autocommit_handler_maker(  # note: change the session scope key if using multiple engines
        commit_on_redirect=True,
    ),
    session_config=AsyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicAsyncConfig(
        version_table_name=settings.db.MIGRATION_DDL_VERSION_TABLE,
        script_config=settings.db.MIGRATION_CONFIG,
        script_location=settings.db.MIGRATION_PATH,
    ),
)
vite = ViteConfig(
    bundle_dir=settings.vite.BUNDLE_DIR,
    resource_dir=settings.vite.RESOURCE_DIR,
    template_dir=settings.vite.TEMPLATE_DIR,
    use_server_lifespan=settings.vite.USE_SERVER_LIFESPAN,
    dev_mode=settings.vite.DEV_MODE,
    hot_reload=settings.vite.HOT_RELOAD,
    is_react=settings.vite.ENABLE_REACT_HELPERS,
    port=settings.vite.PORT,
    host=settings.vite.HOST,
)
inertia = InertiaConfig(
    root_template="site/index.html.j2",
    redirect_unauthorized_to="/login",
    extra_static_page_props={
        "canResetPassword": True,
        "hasTermsAndPrivacyPolicyFeature": True,
        "mustVerifyEmail": True,
    },
    extra_session_page_props={"currentTeam"},
)
session = ServerSideSessionConfig(max_age=3600)
saq = SAQConfig(
    redis=settings.redis.client,
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
_structlog_processors = default_structlog_processors(as_json=_render_as_json)
if settings.app.OPENTELEMETRY_ENABLED:
    _structlog_processors.insert(-1, logfire.StructlogProcessor())
log = StructlogConfig(
    enable_middleware_logging=False,
    structlog_logging_config=StructLoggingConfig(
        log_exceptions="always",
        processors=_structlog_processors,
        logger_factory=default_logger_factory(as_json=_render_as_json),
        standard_lib_logging_config=LoggingConfig(
            root={"level": logging.getLevelName(settings.log.LEVEL), "handlers": ["queue_listener"]},
            formatters={
                "standard": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": default_structlog_standard_lib_processors(as_json=_render_as_json),
                },
            },
            loggers={
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
                "logfire": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "urllib3": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "_granian": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "granian.access": {
                    "propagate": False,
                    "level": settings.log.SQLALCHEMY_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "opentelemetry.sdk.metrics._internal": {
                    "propagate": False,
                    "level": 40,
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

github_oauth2_client = GitHubOAuth2(
    client_id=settings.app.GITHUB_OAUTH2_CLIENT_ID,
    client_secret=settings.app.GITHUB_OAUTH2_CLIENT_SECRET,
)
google_oauth2_client = GoogleOAuth2(
    client_id=settings.app.GOOGLE_OAUTH2_CLIENT_ID,
    client_secret=settings.app.GOOGLE_OAUTH2_CLIENT_SECRET,
)
