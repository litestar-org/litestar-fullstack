"""Litestar application core plugin and dependency assembly."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from functools import partial
from importlib import import_module
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID, uuid4

import structlog
from advanced_alchemy.exceptions import DuplicateKeyError, RepositoryError
from advanced_alchemy.filters import FilterTypes
from advanced_alchemy.service import CursorPagination, OffsetPagination
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.params import Body
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar_email import EmailService
from litestar_queues import QueueService
from litestar_security.accounts import SecurityEvent
from litestar_security.context import Principal

from app import config
from app.__metadata__ import __version__
from app.db import models as m
from app.domain.accounts.security.events import AuditSecurityEventSink, sanitize_event_details
from app.lib.email import AppEmailService
from app.lib.exceptions import (
    ApplicationClientError,
    ApplicationError,
    exception_to_http_response,
)
from app.lib.settings import AppSettings, get_settings, provide_app_settings
from app.lib.validation import ValidationError
from app.server import plugins

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from click import Group
    from litestar import Request
    from litestar.config.app import AppConfig
    from litestar_autowire import AutowireConfig
    from litestar_email import EmailConfig
    from litestar_mcp import AfterToolCallHook, BeforeToolCallHook, MCPConfig
    from litestar_queues import QueueConfig
    from litestar_security import SecurityConfig

__all__ = ("ApplicationCore", "build_mcp_audit_hooks")

logger = structlog.get_logger(__name__)


def _extract_mcp_principal_id(request: Request[Any, Any, Any]) -> str | None:
    principal: object = cast("dict[str, Any]", request.scope).get("user")
    if isinstance(principal, Principal) and principal.is_authenticated and principal.id is not None:
        return str(principal.id)
    return None


def build_mcp_audit_hooks(
    sink: AuditSecurityEventSink,
) -> tuple[BeforeToolCallHook, AfterToolCallHook]:
    """Build observability-only MCP tool call hooks writing redacted telemetry to ``AuditSecurityEventSink``."""

    async def _before_tool_call(
        tool_name: str,
        arguments: dict[str, Any],
        request: Request[Any, Any, Any],
        /,
    ) -> None:
        principal_id = _extract_mcp_principal_id(request)
        correlation_id = request.headers.get("x-request-id") or str(uuid4())
        sanitized_keys = ",".join(sorted(str(k) for k in sanitize_event_details(arguments)))
        event = SecurityEvent(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            operation="mcp.tool.call.started",
            outcome="started",
            account_id=principal_id,
            principal_id=principal_id,
            mechanism="api-key",
            correlation={
                "tool_name": tool_name,
                "correlation_id": correlation_id,
                "argument_keys": sanitized_keys,
            },
        )
        try:
            await logger.ainfo(
                "MCP tool call started",
                tool_name=tool_name,
                principal_id=principal_id,
                correlation_id=correlation_id,
            )
            await sink.emit(event)
        except Exception as exc:  # noqa: BLE001
            await logger.awarning(
                "MCP before_tool_call audit hook failed",
                tool_name=tool_name,
                error_type=type(exc).__name__,
            )

    async def _after_tool_call(
        tool_name: str,
        arguments: dict[str, Any],
        request: Request[Any, Any, Any],
        /,
        *,
        result: Any,
        exception: Exception | None,
        duration: float,
    ) -> None:
        _ = (arguments, result)
        principal_id = _extract_mcp_principal_id(request)
        correlation_id = request.headers.get("x-request-id") or str(uuid4())
        operation = "mcp.tool.call.failed" if exception is not None else "mcp.tool.call.completed"
        outcome = "failure" if exception is not None else "success"
        correlation: dict[str, str] = {
            "tool_name": tool_name,
            "correlation_id": correlation_id,
            "duration_seconds": f"{duration:.6f}",
        }
        if exception is not None:
            correlation["error_type"] = type(exception).__name__
        event = SecurityEvent(
            event_id=str(uuid4()),
            occurred_at=datetime.now(UTC),
            operation=operation,
            outcome=outcome,
            account_id=principal_id,
            principal_id=principal_id,
            mechanism="api-key",
            correlation=correlation,
        )
        try:
            await logger.ainfo(
                "MCP tool call finished",
                tool_name=tool_name,
                principal_id=principal_id,
                outcome=outcome,
                duration_seconds=round(duration, 6),
            )
            await sink.emit(event)
        except Exception as exc:  # noqa: BLE001
            await logger.awarning(
                "MCP after_tool_call audit hook failed",
                tool_name=tool_name,
                error_type=type(exc).__name__,
            )

    return _before_tool_call, _after_tool_call


class ApplicationCore(InitPluginProtocol, CLIPluginProtocol):
    """Primary Litestar initialization and CLI plugin assembling the first-party stack."""

    __slots__ = (
        "app_slug",
        "autowire_config",
        "email_config",
        "mcp_config",
        "queue_config",
        "security_config",
    )

    def __init__(
        self,
        *,
        autowire_config: AutowireConfig | None = None,
        security_config: SecurityConfig[Any] | None = None,
        queue_config: QueueConfig | None = None,
        mcp_config: MCPConfig | None = None,
        email_config: EmailConfig | None = None,
    ) -> None:
        """Initialize the core plugin with optional config overrides for isolated testing."""
        self.app_slug = ""
        self.autowire_config = autowire_config
        self.security_config = security_config
        self.queue_config = queue_config
        self.mcp_config = mcp_config
        self.email_config = email_config

    def on_cli_init(self, cli: Group) -> None:
        """Register application-specific CLI command groups."""
        settings = get_settings()
        self.app_slug = settings.app.slug
        try:
            from app.cli.commands import user_management_group
        except ImportError:
            return
        cli.add_command(user_management_group)

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure OpenAPI, CORS, proxy headers, first-party plugins, DI, and exception handlers."""
        settings = get_settings()
        self.app_slug = settings.app.slug
        app_config.debug = settings.app.DEBUG
        app_config.cors_config = config.cors
        app_config.openapi_config = OpenAPIConfig(
            title=settings.app.NAME,
            version=__version__,
            render_plugins=[ScalarRenderPlugin(version="latest")],
        )

        resolved_mcp = self.mcp_config or config.mcp
        if resolved_mcp.before_tool_call is None and resolved_mcp.after_tool_call is None:
            before_hook, after_hook = build_mcp_audit_hooks(AuditSecurityEventSink(config.alchemy))
            resolved_mcp = replace(
                resolved_mcp,
                before_tool_call=before_hook,
                after_tool_call=after_hook,
            )

        app_config.plugins.extend(
            plugins.build_plugins(
                autowire_config=self.autowire_config,
                security_config=self.security_config,
                queue_config=self.queue_config,
                mcp_config=resolved_mcp,
                email_config=self.email_config,
            )
        )

        active_security = self.security_config or config.security
        if active_security.local_auth is not None:
            from contextlib import suppress

            from app.domain.accounts.security import build_session_store

            if isinstance(app_config.stores, dict):
                app_config.stores.setdefault("sessions", build_session_store(config.alchemy))
            elif app_config.stores is not None:
                with suppress(KeyError):
                    app_config.stores.register("sessions", build_session_store(config.alchemy), allow_override=False)
            else:
                app_config.stores = {"sessions": build_session_store(config.alchemy)}
            app_config.middleware.append(config.session_middleware)
            if app_config.csrf_config is None:
                app_config.csrf_config = config.csrf

        if settings.server.LITESTAR_TRUSTED_PROXIES:
            proxy_wrapper: Any = vars(import_module("granian.utils.proxies"))["wrap_asgi_with_proxy_headers"]
            app_config.middleware.append(
                partial(
                    proxy_wrapper,
                    trusted_hosts=settings.server.LITESTAR_TRUSTED_PROXIES,
                )
            )

        active_email_config = self.email_config or config.email

        async def provide_mailer() -> AsyncIterator[EmailService]:
            async with active_email_config.provide_service() as service:
                yield service

        app_config.dependencies.update(
            {
                "settings": Provide(provide_app_settings, sync_to_thread=False),
                "mailer": Provide(provide_mailer),
                "app_mailer": Provide(AppEmailService, sync_to_thread=False),
            }
        )

        app_config.signature_namespace.update(
            {
                "FilterTypes": FilterTypes,
                "OffsetPagination": OffsetPagination,
                "CursorPagination": CursorPagination,
                "AppSettings": AppSettings,
                "AppEmailService": AppEmailService,
                "EmailService": EmailService,
                "QueueService": QueueService,
                "m": m,
                "User": m.User,
                "UUID": UUID,
                "datetime": datetime,
                "RequestEncodingType": RequestEncodingType,
                "Body": Body,
            }
        )

        handlers: dict[Any, Any] = cast("Any", app_config).exception_handlers
        handlers.update(
            {
                ApplicationError: exception_to_http_response,
                ApplicationClientError: exception_to_http_response,
                ValidationError: exception_to_http_response,
                RepositoryError: exception_to_http_response,
                DuplicateKeyError: exception_to_http_response,
            }
        )

        return app_config
