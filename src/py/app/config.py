"""Module-level Litestar plugin configuration singletons."""

from __future__ import annotations

from litestar.exceptions import HTTPException, NotFoundException
from litestar.plugins.problem_details import ProblemDetailsConfig
from litestar_asyncapi import AsyncAPIConfig, ChannelDefinition, MessageDefinition, OperationDefinition
from litestar_autowire import AutowireConfig
from litestar_security import required

from app.domain.accounts.security.config import (
    build_csrf_config,
    build_security_config,
    build_session_middleware,
)
from app.domain.system.jobs import QueueTaskEventPayload
from app.lib.exceptions import to_problem_details
from app.lib.settings import get_settings

_settings = get_settings()

cors = _settings.app.get_cors_config()
alchemy = _settings.db.get_config()
vite = _settings.vite.get_config()
problem_details = ProblemDetailsConfig(
    enable_for_all_http_exceptions=True,
    exception_to_problem_detail_map={HTTPException: to_problem_details, NotFoundException: to_problem_details},
)
"""Renders every HTTP error as one problem details envelope.

``enable_for_all_http_exceptions`` is what tells ``litestar-security`` to document its routes' errors as
``application/problem+json``; the map then replaces the plugin's own conversion with ``to_problem_details``.

``NotFoundException`` is mapped on its own because the Vite plugin otherwise answers it with an empty body.
"""
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
    "cors",
    "csrf",
    "email",
    "log",
    "mcp",
    "problem_details",
    "queues",
    "security",
    "session_middleware",
    "vite",
)
