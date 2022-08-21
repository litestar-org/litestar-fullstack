# Standard Library

import logging.config
import re
from functools import lru_cache
from logging import Filter as LoggingFilter
from queue import Queue
from typing import TYPE_CHECKING, Any, Final, Generic, List, TypeVar

import picologging
from gunicorn.glogging import Logger as GunicornLogger
from picologging import LogRecord
from picologging.handlers import QueueHandler, QueueListener
from rich.console import Console
from rich.logging import RichHandler as _RichHandler
from starlette.status import HTTP_200_OK
from starlite import LoggingConfig

from pyspa.config.application import ApiPaths, settings

DEFAULT_LOG_NAME: Final = "pyspa"


class RichHandler(_RichHandler):
    """Rich Handler Config"""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        super().__init__(
            rich_tracebacks=settings.app.LOG_LEVEL.lower() == "debug",
            console=Console(markup=True),
            tracebacks_suppress=[
                "click",
                "typer",
                "uvloop",
                "uvicorn",
                "gunicorn",
                "starlette",
                "starlite",
                "sqlalchemy",
                "anyio",
                "asyncio",
            ],
            markup=True,
            show_path=False,
            omit_repeated_times=False,
        )


class AccessLogFilter(LoggingFilter):
    """
    For filtering log events based on request path.

    Parameters
    ----------
    path_re : str Regex string,
        drops log event if the path of the request matches the regex.
    args : Any
    kwargs : Any
        Args and kwargs passed through to `logging.Filter`.
    """

    def __init__(self, *args: Any, path_re: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.path_filter = re.compile(path_re)

    def filter(self, record: logging.LogRecord) -> bool:
        *_, req_path, _, status_code = record.args  # type: ignore
        if self.path_filter.match(req_path) and status_code == HTTP_200_OK:  # type: ignore
            return False
        return True


class QueueListenerHandler(QueueHandler):  # type: ignore
    """
    Configures queue listener and handler to support non-blocking logging configuration.
    """

    def __init__(
        self,
        handlers: List[Any],
        respect_handler_level: bool = False,
        queue: Queue[LogRecord] = Queue(-1),
    ):
        super().__init__(queue)
        self.handlers = _resolve_handlers(handlers)
        self._listener: QueueListener = QueueListener(
            self.queue, *self.handlers, respect_handler_level=respect_handler_level
        )
        self._listener.start()


class StubbedGunicornLogger(GunicornLogger):  # type: ignore
    """Customized Gunicorn Logger"""

    def setup(self, cfg: Any) -> None:
        """Configures logger"""
        self.handler = RichHandler()
        self.error_logger = picologging.getLogger("gunicorn.error")
        self.error_logger.addHandler(self.handler)
        self.access_logger = picologging.getLogger("gunicorn.access")
        self.access_logger.addHandler(self.handler)


log_config = LoggingConfig(
    root={"level": settings.app.LOG_LEVEL, "handlers": ["queue_listener"]},
    filters={
        "health_filter": {
            "()": AccessLogFilter,
            "path_re": f"^{ApiPaths.HEALTH}$",
        }
    },
    handlers={
        "console": {
            "class": "pyspa.config.logging.RichHandler",
            "level": "DEBUG",
            "formatter": "standard",
        },
        "queue_listener": {
            "class": "starlite.logging.picologging.QueueListenerHandler",
            "handlers": ["cfg://handlers.console"],
        },
    },
    formatters={
        "standard": {"format": "%(levelname)s - %(asctime)s - %(name)s - %(message)s"}
    },
    loggers={
        "pyspa": {
            "propagate": True,
        },
        "gunicorn.error": {
            "propagate": True,
        },
        "uvicorn.access": {
            "propagate": True,
            "filters": ["health_filter"],
        },
        "uvicorn.error": {
            "propagate": True,
        },
        "sqlalchemy.engine": {
            "propagate": True,
        },
        "starlite": {
            "level": "WARNING",
            "propagate": True,
        },
    },
)


@lru_cache(maxsize=1)
def get_logger(name: str = DEFAULT_LOG_NAME) -> picologging.Logger:
    """
    Returns a Configured Logger
    """
    log_config.configure()
    return picologging.getLogger(name)


def _resolve_handlers(handlers: List[Any]) -> List[Any]:
    """
    Converts list of string of handlers to the object of respective handler.
    Indexing the list performs the evaluation of the object.
    """
    return [handlers[i] for i in range(len(handlers))]
