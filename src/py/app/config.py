"""Module-level Litestar plugin configuration singletons."""

from __future__ import annotations

import structlog
from litestar_asyncapi import AsyncAPIConfig
from litestar_autowire import AutowireConfig
from litestar_security import required

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
    title=_settings.app.NAME,
    version=_settings.app.VERSION,
    include_sse_routes=True,
    include_websocket_routes=True,
)
autowire = AutowireConfig(
    domain_packages=["app.domain"],
    integrations=["queues"],
)
security = _settings.security.get_config(_settings.app)
mcp = _settings.mcp.get_config(
    auth=required("api-key") if security.api_key is not None else None,
)

__all__ = (
    "alchemy",
    "asyncapi",
    "autowire",
    "compression",
    "cors",
    "email",
    "log",
    "mcp",
    "problem_details",
    "queues",
    "security",
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
