import logging
import re
from typing import Any

from starlette.status import HTTP_200_OK
from starlite.config import LoggingConfig

from pyspa.config.application import settings
from pyspa.config.paths import urls


class AccessLogFilter(logging.Filter):
    """For filtering log events based on request path.

    Parameters
    ----------
    path_re : str
        Regex string, if the path of the request matches the regex the log event is dropped.
    args : Any
    kwargs : Any
        Args and kwargs passed through to `logging.Filter`.
    """

    def __init__(self, *args: Any, path_re: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.path_filter = re.compile(path_re)

    def filter(self, record: logging.LogRecord) -> bool:
        *_, req_path, _, status_code = record.args  # type:ignore[misc]
        if (
            self.path_filter.match(req_path)  # type:ignore[arg-type]
            and status_code == HTTP_200_OK
        ):
            return False
        return True


log_config = LoggingConfig(
    root={"level": settings.app.LOG_LEVEL, "handlers": ["queue_listener"]},
    filters={
        "health_filter": {
            "()": AccessLogFilter,
            "path_re": f"^{urls.HEALTH}$",
        }
    },
    handlers={
        "console": {
            "class": "rich.logging.RichHandler",
            "markup": True,
            "rich_tracebacks": True,
            "omit_repeated_times": False,
        },
        "queue_listener": {
            "class": "starlite.QueueListenerHandler",
            "handlers": ["cfg://handlers.console"],
        },
    },
    formatters={
        "standard": {"format": "%(message)s"},
    },
    loggers={
        "uvicorn.access": {
            "propagate": True,
            "filters": ["health_filter"],
            "level": settings.server.UVICORN_LOG_LEVEL.lower(),
        },
        "uvicorn.error": {"propagate": True, "level": settings.server.UVICORN_LOG_LEVEL.lower()},
        "sqlalchemy": {
            "propagate": True,
            "level": "WARNING",
        },
        "starlite": {
            "level": "WARNING",
            "propagate": True,
        },
        "pydantic_openapi_schema": {
            "propagate": True,
            "level": "WARNING",
            "handlers": ["queue_listener"],
        },
    },
)
log_config.configure()
"""
Pre-configured log config for application.
"""
