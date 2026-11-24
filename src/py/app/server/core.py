"""Litestar application core plugin and dependency assembly."""

from __future__ import annotations

from datetime import datetime
from functools import partial
from importlib import import_module
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

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

from app import config
from app.__metadata__ import __version__
from app.db import models as m
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
    from litestar.config.app import AppConfig
    from litestar_autowire import AutowireConfig
    from litestar_email import EmailConfig
    from litestar_mcp import MCPConfig
    from litestar_queues import QueueConfig
    from litestar_security import SecurityConfig

__all__ = ("ApplicationCore",)


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

        app_config.plugins.extend(
            plugins.build_plugins(
                autowire_config=self.autowire_config,
                security_config=self.security_config,
                queue_config=self.queue_config,
                mcp_config=self.mcp_config,
                email_config=self.email_config,
            )
        )

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
