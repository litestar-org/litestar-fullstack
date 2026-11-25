"""Litestar application core plugin and dependency assembly."""

from __future__ import annotations

from contextlib import suppress
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
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from litestar_email import EmailService
from litestar_queues import QueueService
from litestar_security.accounts import SecurityEvent
from litestar_security.context import Principal

from app import config
from app.__metadata__ import __version__
from app.db import models as m
from app.domain.accounts.security import AuditSecurityEventSink, require_application_access, sanitize_event_details
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


def build_mcp_audit_hooks(
    sink: AuditSecurityEventSink,
) -> tuple[BeforeToolCallHook, AfterToolCallHook]:
    """Build observability-only MCP tool call hooks writing redacted telemetry to ``AuditSecurityEventSink``.

    Returns:
        Pair of ``(before_tool_call, after_tool_call)`` async hook callables.
    """

    async def _before_tool_call(
        tool_name: str,
        arguments: dict[str, Any],
        request: Request[Any, Any, Any],
        /,
    ) -> None:
        principal_id = _extract_mcp_principal_id(request)
        correlation_id = _mcp_correlation_id(request)
        event = _mcp_tool_call_event(
            "mcp.tool.call.started",
            outcome="started",
            principal_id=principal_id,
            correlation={
                "tool_name": tool_name,
                "correlation_id": correlation_id,
                "argument_keys": ",".join(sorted(str(key) for key in sanitize_event_details(arguments))),
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
        outcome = "failure" if exception is not None else "success"
        correlation = {
            "tool_name": tool_name,
            "correlation_id": _mcp_correlation_id(request),
            "duration_seconds": f"{duration:.6f}",
        }
        if exception is not None:
            correlation["error_type"] = type(exception).__name__
        event = _mcp_tool_call_event(
            "mcp.tool.call.failed" if exception is not None else "mcp.tool.call.completed",
            outcome=outcome,
            principal_id=principal_id,
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
        """Configure OpenAPI, CORS, proxy headers, first-party plugins, the access guard, DI, and exception handlers.

        Returns:
            Updated Litestar ``AppConfig``.
        """
        settings = get_settings()
        self.app_slug = settings.app.slug
        app_config.debug = settings.app.DEBUG
        app_config.cors_config = config.cors
        app_config.openapi_config = OpenAPIConfig(
            title=settings.app.NAME,
            version=__version__,
            render_plugins=[ScalarRenderPlugin(version="latest")],
        )
        app_config.plugins.extend(
            plugins.build_plugins(
                autowire_config=self.autowire_config,
                security_config=self.security_config,
                queue_config=self.queue_config,
                mcp_config=self._resolve_mcp_config(mcp_enabled=settings.mcp.ENABLED),
                email_config=self.email_config,
            )
        )
        app_config.guards.append(require_application_access)  # pyright: ignore[reportUnknownMemberType]
        self._enable_local_auth(app_config)
        self._trust_proxy_headers(app_config, settings.server.LITESTAR_TRUSTED_PROXIES)
        self._register_dependencies(app_config)
        self._register_exception_handlers(app_config)
        return app_config

    def _resolve_mcp_config(self, *, mcp_enabled: bool) -> MCPConfig | None:
        if self.mcp_config is None and not mcp_enabled:
            return None
        mcp_config = self.mcp_config or config.mcp
        if mcp_config.before_tool_call is not None or mcp_config.after_tool_call is not None:
            return mcp_config
        before_hook, after_hook = build_mcp_audit_hooks(AuditSecurityEventSink(config.alchemy))
        return replace(mcp_config, before_tool_call=before_hook, after_tool_call=after_hook)

    def _enable_local_auth(self, app_config: AppConfig) -> None:
        security_config = self.security_config or config.security
        if security_config.local_auth is None:
            return
        self._register_session_store(app_config)
        app_config.middleware.append(config.session_middleware)
        if app_config.csrf_config is None:
            app_config.csrf_config = config.csrf

    @staticmethod
    def _register_session_store(app_config: AppConfig) -> None:
        from app.domain.accounts.security import build_session_store

        if isinstance(app_config.stores, dict):
            app_config.stores.setdefault("sessions", build_session_store(config.alchemy))
        elif app_config.stores is not None:
            with suppress(KeyError, ValueError):
                app_config.stores.register("sessions", build_session_store(config.alchemy), allow_override=False)
        else:
            app_config.stores = {"sessions": build_session_store(config.alchemy)}

    @staticmethod
    def _trust_proxy_headers(app_config: AppConfig, trusted_proxies: list[str]) -> None:
        if not trusted_proxies:
            return
        proxy_wrapper: Any = vars(import_module("granian.utils.proxies"))["wrap_asgi_with_proxy_headers"]
        app_config.middleware.append(partial(proxy_wrapper, trusted_hosts=trusted_proxies))

    def _register_dependencies(self, app_config: AppConfig) -> None:
        email_config = self.email_config or config.email

        def provide_mailer() -> EmailService:
            return email_config.get_service()

        app_config.dependencies.update(
            {
                "settings": Provide(provide_app_settings, sync_to_thread=False),
                "mailer": Provide(provide_mailer, sync_to_thread=False),
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

    @staticmethod
    def _register_exception_handlers(app_config: AppConfig) -> None:
        handlers: dict[Any, Any] = cast("Any", app_config).exception_handlers
        handlers.update(
            {
                ApplicationError: exception_to_http_response,
                ApplicationClientError: exception_to_http_response,
                ValidationError: exception_to_http_response,
                RepositoryError: exception_to_http_response,
                DuplicateKeyError: exception_to_http_response,
                HTTP_500_INTERNAL_SERVER_ERROR: exception_to_http_response,
            }
        )


def _extract_mcp_principal_id(request: Request[Any, Any, Any]) -> str | None:
    principal: object = cast("dict[str, Any]", request.scope).get("user")
    if isinstance(principal, Principal) and principal.is_authenticated and principal.id is not None:
        return str(principal.id)
    return None


def _mcp_correlation_id(request: Request[Any, Any, Any]) -> str:
    supplied = request.headers.get("x-request-id")
    if supplied:
        return supplied
    state = cast("dict[str, Any]", request.scope).setdefault("state", {})
    return cast("str", state.setdefault("mcp_correlation_id", str(uuid4())))


def _mcp_tool_call_event(
    operation: str,
    *,
    outcome: str,
    principal_id: str | None,
    correlation: dict[str, str],
) -> SecurityEvent:
    return SecurityEvent(
        event_id=str(uuid4()),
        occurred_at=datetime.now(UTC),
        operation=operation,
        outcome=outcome,
        account_id=principal_id,
        principal_id=principal_id,
        mechanism="api-key",
        correlation=correlation,
    )
