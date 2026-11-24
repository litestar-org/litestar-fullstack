"""Module-level Litestar plugin configuration singletons."""

from __future__ import annotations

import structlog
from litestar_asyncapi import AsyncAPIConfig, ChannelDefinition, MessageDefinition, OperationDefinition
from litestar_autowire import AutowireConfig
from litestar_security import required

from app.domain.accounts.security.config import (
    build_csrf_config,
    build_security_config,
    build_session_middleware,
)
from app.domain.system.jobs import QueueTaskEventPayload
from app.lib.settings import get_settings

_settings = get_settings()

compression = _settings.app.get_compression_config()
cors = _settings.app.get_cors_config()
alchemy = _settings.db.get_config()
vite = _settings.vite.get_config()
problem_details = _settings.app.get_problem_details_config()
log = _settings.log.get_structlog_config()
email = _settings.email.get_config()
queues = _settings.queues.get_config(
    alchemy_config=alchemy,
    db_settings=_settings.db,
    app_settings=_settings.app,
)
asyncapi = AsyncAPIConfig(
    title=f"{_settings.app.NAME} Events",
    version=_settings.app.VERSION,
    include_sse_routes=True,
    include_websocket_routes=True,
    channels=[
        ChannelDefinition(
            key="queue_events",
            address=_settings.queues.STREAM_PATH,
            description="Live background queue task lifecycle and progress events.",
            operations=[
                OperationDefinition(
                    action="receive",
                    operation_id="receiveQueueEvents",
                    messages=[
                        MessageDefinition(
                            name="QueueTaskEvent",
                            payload=QueueTaskEventPayload,
                        )
                    ],
                )
            ],
        )
    ],
)
autowire = AutowireConfig(
    domain_packages=["app.domain"],
    integrations=["queues"],
)
csrf = build_csrf_config(_settings)
session_middleware = build_session_middleware(_settings)
security = build_security_config(_settings, alchemy)
mcp = _settings.mcp.get_config(auth=required("api-key"))

__all__ = (
    "alchemy",
    "asyncapi",
    "autowire",
    "compression",
    "cors",
    "csrf",
    "email",
    "log",
    "mcp",
    "problem_details",
    "queues",
    "security",
    "session_middleware",
    "setup_logging",
    "vite",
)


def setup_logging() -> None:
    """Configure stdlib and structlog loggers from application log settings."""
    if log.structlog_logging_config.standard_lib_logging_config:
        log.structlog_logging_config.standard_lib_logging_config.configure()
    log.structlog_logging_config.configure()
    structlog.configure(
        cache_logger_on_first_use=True,
        logger_factory=log.structlog_logging_config.logger_factory,
        processors=log.structlog_logging_config.processors,
        wrapper_class=structlog.make_filtering_bound_logger(_settings.log.LEVEL),
    )
