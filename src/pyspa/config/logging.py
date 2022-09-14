from starlite.config import LoggingConfig

from pyspa.utils.log.extensions import PicologgingAccessLogFilter

log_config = LoggingConfig(
    filters={
        "health_filter": {
            "()": PicologgingAccessLogFilter,
            "path_re": "^/health$",
        }
    },
    handlers={
        "console": {
            "class": "pyspa.utils.log.extensions.RichPicologgingHandler",
            "markup": True,
            "rich_tracebacks": True,
            "omit_repeated_times": False,
        },
        "queue_listener": {
            "class": "starlite.logging.picologging.QueueListenerHandler",
            "handlers": ["cfg://handlers.console"],
        },
    },
    formatters={
        "standard": {"format": "%(message)s"},
    },
    loggers={
        "pyspa": {
            "propagate": True,
            "filters": ["health_filter"],
            "level": "INFO",
        },
        "uvicorn.access": {
            "propagate": True,
            "filters": ["health_filter"],
        },
        "uvicorn.error": {
            "propagate": True,
        },
        "sqlalchemy": {
            "propagate": True,
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
