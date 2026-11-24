"""Unit tests for QueueSettings, AsyncAPIConfig channel contract, and AutowirePlugin task discovery."""

from __future__ import annotations

import json
from typing import Any, cast

from litestar import Litestar
from litestar_asyncapi import AsyncAPIPlugin
from litestar_autowire import AutowireConfig, AutowirePlugin, clear_autowire_cache
from litestar_queues import QueueConfig, QueuePlugin, WorkerConfig, get_task_registry
from litestar_queues.backends.advanced_alchemy import SQLAlchemyBackendConfig

from app import config as app_config
from app.db import models as m
from app.lib.settings import AppSettings, DatabaseSettings, QueueSettings


def test_queue_settings_worker_wakeups_and_backend_models() -> None:
    pg_db = DatabaseSettings(URL="postgresql+asyncpg://user:pass@localhost:5432/app")
    sqlite_db = DatabaseSettings(URL="sqlite+aiosqlite:///:memory:")
    app_settings = AppSettings(SECRET_KEY="queue-test-secret", ENABLE_INSTRUMENTATION=True)

    q_default = QueueSettings()
    assert q_default.resolve_worker_wakeups(pg_db) is True
    assert q_default.resolve_worker_wakeups(sqlite_db) is False

    q_force_true = QueueSettings(WORKER_WAKEUPS=True)
    assert q_force_true.resolve_worker_wakeups(sqlite_db) is False
    assert q_force_true.resolve_worker_wakeups(pg_db) is True

    pg_cfg = q_default.get_config(
        alchemy_config=pg_db.get_config(),
        db_settings=pg_db,
        app_settings=app_settings,
    )
    assert isinstance(pg_cfg.queue_backend, SQLAlchemyBackendConfig)
    assert pg_cfg.queue_backend.model_class is m.QueueTask
    assert pg_cfg.queue_backend.event_history_model_class is m.QueueEventHistory
    assert pg_cfg.queue_backend.maintenance_model_class is m.QueueMaintenance
    assert pg_cfg.queue_backend.task_reservation_model_class is m.QueueTaskReservation
    assert pg_cfg.queue_backend.worker_wakeups is True
    assert pg_cfg.worker.queues == ("default", "emails", "reports", "maintenance")
    assert pg_cfg.events is not None
    assert pg_cfg.events.stream is not None
    assert pg_cfg.events.stream.path == "/api/queues/events"
    assert pg_cfg.events.stream.transports == {"sse", "websocket"}
    assert pg_cfg.events.stream.opt is not None
    assert "auth" in pg_cfg.events.stream.opt
    assert pg_cfg.scheduler_canary_task == "system.scheduler_canary"
    assert pg_cfg.error_sanitizer is not None
    sanitized = pg_cfg.error_sanitizer(RuntimeError("secret password leaked"), cast("Any", None))
    assert sanitized == "Task failed: RuntimeError"
    assert "secret" not in sanitized

    q_no_stream = QueueSettings(STREAM_ENABLED=False)
    no_stream_cfg = q_no_stream.get_config(
        alchemy_config=sqlite_db.get_config(),
        db_settings=sqlite_db,
        app_settings=app_settings,
    )
    assert isinstance(no_stream_cfg.queue_backend, SQLAlchemyBackendConfig)
    assert no_stream_cfg.queue_backend.worker_wakeups is False
    assert no_stream_cfg.events is not None
    assert no_stream_cfg.events.stream is None


def test_asyncapi_channel_contract_and_autowire_queue_discovery() -> None:
    clear_autowire_cache()
    asyncapi_plugin = AsyncAPIPlugin(config=app_config.asyncapi)
    app = Litestar(
        plugins=[
            QueuePlugin(config=QueueConfig(queue_backend="memory", worker=WorkerConfig(placement="asgi"))),
            asyncapi_plugin,
            AutowirePlugin(
                config=AutowireConfig(
                    domain_packages=["app.domain.accounts", "app.domain.system"],
                    integrations=["queues"],
                    discover_controllers=False,
                    discover_listeners=False,
                )
            ),
        ]
    )
    schema = json.loads(asyncapi_plugin.get_asyncapi_json(app))
    channels = schema.get("channels", {})
    assert "queue_events" in channels
    assert channels["queue_events"]["address"] == "/api/queues/events"

    schemas = schema.get("components", {}).get("schemas", {})
    payload_schema = next(
        (s for name, s in schemas.items() if "QueueTaskEventPayload" in name),
        None,
    )
    assert payload_schema is not None
    props = set(payload_schema.get("properties", {}).keys())
    assert {"taskId", "taskName", "queue", "status", "progress", "total", "message", "timestamp"}.issubset(props)

    registry = get_task_registry()
    for expected in (
        "system.cleanup_auth_tokens",
        "system.scheduler_canary",
        "reports.export_team_summary",
        "accounts.refresh_oauth_tokens",
        "email.send_verification",
        "email.send_password_reset",
        "email.send_password_reset_confirmation",
        "email.send_welcome",
        "email.send_team_invitation",
    ):
        assert expected in registry
