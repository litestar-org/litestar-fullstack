import logging
from pathlib import Path
from typing import cast

import structlog
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.exceptions import (
    NotAuthorizedException,
    PermissionDeniedException,
)
from litestar.logging.config import (
    LoggingConfig,
    StructLoggingConfig,
    default_logger_factory,
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
from litestar_saq import QueueConfig, SAQConfig
from litestar_vite import ViteConfig

from app.lib import log as log_conf
from app.lib.settings import get_settings
from app.lib.worker import after_process as worker_after_process
from app.lib.worker import before_process as worker_before_process
from app.lib.worker import on_shutdown as worker_on_shutdown
from app.lib.worker import on_startup as worker_on_startup

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
    before_send_handler="autocommit",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    alembic_config=AlembicAsyncConfig(
        version_table_name=settings.db.MIGRATION_DDL_VERSION_TABLE,
        script_config=settings.db.MIGRATION_CONFIG,
        script_location=settings.db.MIGRATION_PATH,
    ),
)
vite = ViteConfig(
    root_dir=Path(__file__).parent.parent.parent / "js",
    bundle_dir=settings.vite.BUNDLE_DIR,
    resource_dir=settings.vite.RESOURCE_DIR,
    use_server_lifespan=settings.vite.USE_SERVER_LIFESPAN,
    dev_mode=settings.vite.DEV_MODE,
    hot_reload=settings.vite.HOT_RELOAD,
    is_react=settings.vite.ENABLE_REACT_HELPERS,
    port=settings.vite.PORT,
    host=settings.vite.HOST,
)
saq = SAQConfig(
    web_enabled=settings.saq.WEB_ENABLED,
    worker_processes=settings.saq.PROCESSES,
    use_server_lifespan=settings.saq.USE_SERVER_LIFESPAN,
    queue_configs=[
        QueueConfig(
            name="background-tasks",
            dsn=settings.db.URL.replace("postgresql+psycopg", "postgresql"),
            broker_options={
                "stats_table": "task_queue_stats",
                "jobs_table": "task_queue",
                "versions_table": "task_queue_ddl_version",
            },
            tasks=[],
            scheduled_tasks=[],
            concurrency=20,
            startup=worker_on_startup,
            shutdown=worker_on_shutdown,
            before_process=worker_before_process,
            after_process=worker_after_process,
        )
    ],
)
templates = TemplateConfig(engine=JinjaTemplateEngine(directory=settings.vite.TEMPLATE_DIR))
problem_details = ProblemDetailsConfig(enable_for_all_http_exceptions=True)


log = StructlogConfig(
    enable_middleware_logging=False,
    structlog_logging_config=StructLoggingConfig(
        log_exceptions="always",
        processors=log_conf.structlog_processors(as_json=not log_conf.is_tty()),  # type: ignore[has-type,unused-ignore]
        logger_factory=default_logger_factory(as_json=not log_conf.is_tty()),  # type: ignore[has-type,unused-ignore]
        disable_stack_trace={404, 401, 403, NotAuthorizedException, PermissionDeniedException},
        standard_lib_logging_config=LoggingConfig(
            log_exceptions="always",
            disable_stack_trace={404, 401, 403, NotAuthorizedException, PermissionDeniedException},
            root={"level": logging.getLevelName(settings.log.LEVEL), "handlers": ["queue_listener"]},
            formatters={
                "standard": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": log_conf.stdlib_logger_processors(as_json=not log_conf.is_tty()),  # type: ignore[has-type,unused-ignore]
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
                "opentelemetry.sdk.metrics._internal": {
                    "propagate": False,
                    "level": 40,
                    "handlers": ["queue_listener"],
                },
                "_granian": {
                    "propagate": False,
                    "level": settings.log.ASGI_ERROR_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "granian.server": {
                    "propagate": False,
                    "level": settings.log.ASGI_ERROR_LEVEL,
                    "handlers": ["queue_listener"],
                },
                "granian.access": {
                    "propagate": False,
                    "level": settings.log.ASGI_ACCESS_LEVEL,
                    "handlers": ["queue_listener"],
                },
            },
        ),
    ),
    middleware_logging_config=LoggingMiddlewareConfig(
        request_log_fields=settings.log.REQUEST_FIELDS,
        response_log_fields=settings.log.RESPONSE_FIELDS,
    ),
)


def setup_logging() -> None:
    """Return a configured logger for the given name.

    Args:
        args: positional arguments to pass to the bound logger instance
        kwargs: keyword arguments to pass to the bound logger instance
    """
    if log.structlog_logging_config.standard_lib_logging_config:
        log.structlog_logging_config.standard_lib_logging_config.configure()
    log.structlog_logging_config.configure()
    structlog.configure(
        cache_logger_on_first_use=True,
        logger_factory=log.structlog_logging_config.logger_factory,
        processors=log.structlog_logging_config.processors,
        wrapper_class=structlog.make_filtering_bound_logger(settings.log.LEVEL),
    )
