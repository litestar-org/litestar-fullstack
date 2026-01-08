from functools import cache

import structlog
from litestar_saq import SAQConfig

from app.lib.settings import get_settings

_settings = get_settings()

compression = _settings.app.get_compression_config()
cors = _settings.app.get_cors_config()
alchemy = _settings.db.get_config()
vite = _settings.vite.get_config()
problem_details = _settings.app.get_problem_details_config()
log = _settings.log.get_structlog_config()
email = _settings.email.get_config()


@cache
def get_saq_config() -> SAQConfig:
    """Get SAQ config lazily to avoid Redis connection during build."""
    return _settings.saq.get_config()


def setup_logging() -> None:
    """Return a configured logger for the given name."""
    if log.structlog_logging_config.standard_lib_logging_config:
        log.structlog_logging_config.standard_lib_logging_config.configure()
    log.structlog_logging_config.configure()
    structlog.configure(
        cache_logger_on_first_use=True,
        logger_factory=log.structlog_logging_config.logger_factory,
        processors=log.structlog_logging_config.processors,
        wrapper_class=structlog.make_filtering_bound_logger(_settings.log.LEVEL),
    )
