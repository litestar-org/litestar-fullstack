from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import get_settings

if TYPE_CHECKING:
    from litestar.contrib.opentelemetry import OpenTelemetryConfig

settings = get_settings()


def configure_instrumentation() -> OpenTelemetryConfig:
    """Initialize Open Telemetry configuration."""
    import logfire
    from litestar.contrib.opentelemetry import OpenTelemetryConfig
    from opentelemetry import metrics
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    logfire.configure()
    SQLAlchemyInstrumentor().instrument(engine=settings.db.engine.sync_engine)
    return OpenTelemetryConfig(meter=metrics.get_meter(__name__))
