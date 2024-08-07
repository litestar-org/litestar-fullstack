from __future__ import annotations

import copy
from typing import TYPE_CHECKING, ClassVar

from litestar.contrib.opentelemetry import (
    OpenTelemetryConfig,
    OpenTelemetryInstrumentationMiddleware,
)
from litestar.middleware import AbstractMiddleware

from app.config import get_settings

if TYPE_CHECKING:
    from litestar.types import ASGIApp
    from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

settings = get_settings()


class OpenTelemetrySingletonMiddleware(OpenTelemetryInstrumentationMiddleware):
    """OpenTelemetry Singleton Middleware

    https://github.com/litestar-org/litestar/issues/3056
    """

    __open_telemetry_middleware__: ClassVar[OpenTelemetryMiddleware]

    def __init__(self, app: ASGIApp, config: OpenTelemetryConfig) -> None:
        cls = self.__class__
        if singleton_middleware := getattr(cls, "__open_telemetry_middleware__", None):
            AbstractMiddleware.__init__(
                self,
                app,
                scopes=config.scopes,
                exclude=config.exclude,
                exclude_opt_key=config.exclude_opt_key,
            )
            self.open_telemetry_middleware = copy.copy(singleton_middleware)
            self.open_telemetry_middleware.app = app
        else:
            super().__init__(app, config)
            cls.__open_telemetry_middleware__ = self.open_telemetry_middleware


def configure_instrumentation() -> OpenTelemetryConfig:
    """Initialize Open Telemetry configuration."""
    import logfire
    from opentelemetry import metrics
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(engine=settings.db.engine.sync_engine)
    logfire.configure()
    return OpenTelemetryConfig(meter=metrics.get_meter(__name__), middleware_class=OpenTelemetrySingletonMiddleware)
