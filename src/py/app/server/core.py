# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar.security.jwt import OAuth2Login

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from click import Group
    from litestar.config.app import AppConfig
    from litestar.datastructures import State

    from app.lib.email import AppEmailService


T = TypeVar("T")


async def get_mailer_dependency(state: State) -> AsyncGenerator[AppEmailService, None]:
    """Provide the app email service.

    Args:
        state: The application state.

    Yields:
        The configured AppEmailService.
    """
    from app.lib.email import AppEmailService

    email_config = state.mailer
    async with email_config.provide_service() as mailer:
        yield AppEmailService(mailer=mailer)


class ApplicationCore(InitPluginProtocol, CLIPluginProtocol):
    """Application core configuration plugin.

    This class is responsible for configuring the main Litestar application with our routes, guards, and various plugins

    """

    __slots__ = ("app_slug",)
    app_slug: str

    def on_cli_init(self, cli: Group) -> None:
        from app.cli.commands import user_management_group
        from app.lib.settings import get_settings

        settings = get_settings()
        self.app_slug = settings.app.slug
        cli.add_command(user_management_group)

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Configure application for use with SQLAlchemy.

        Args:
            app_config: The :class:`AppConfig <litestar.config.app.AppConfig>` instance.

        Returns:
            The configured app config.
        """

        from datetime import datetime
        from uuid import UUID

        from advanced_alchemy.exceptions import DuplicateKeyError, RepositoryError
        from httpx_oauth.oauth2 import OAuth2Token
        from litestar.enums import RequestEncodingType
        from litestar.params import Body
        from litestar.security.jwt import Token
        from litestar_email import EmailService

        from app import config
        from app.__metadata__ import __version__
        from app.db import models as m
        from app.domain.accounts.guards import auth, provide_user
        from app.lib.email import AppEmailService
        from app.lib.exceptions import (
            ApplicationClientError,
            ApplicationError,
            exception_to_http_response,
        )
        from app.lib.settings import AppSettings, get_settings, provide_app_settings
        from app.lib.validation import ValidationError
        from app.server import plugins

        settings = get_settings()
        self.app_slug = settings.app.slug
        app_config.debug = settings.app.DEBUG
        app_config.openapi_config = OpenAPIConfig(
            title=settings.app.NAME,
            version=__version__,
            components=[auth.openapi_components],
            security=[auth.security_requirement],
            render_plugins=[ScalarRenderPlugin(version="latest")],
        )
        app_config = auth.on_app_init(app_config)
        app_config.cors_config = config.cors

        app_config.plugins.extend(
            [
                plugins.structlog,
                plugins.granian,
                plugins.alchemy,
                plugins.vite,
                plugins.get_saq_plugin(),
                plugins.problem_details,
                plugins.oauth2_provider,
                plugins.email,
                plugins.domain,
            ],
        )

        app_config.signature_namespace.update(
            {
                "Token": Token,
                "OAuth2Login": OAuth2Login,
                "RequestEncodingType": RequestEncodingType,
                "Body": Body,
                "m": m,
                "UUID": UUID,
                "datetime": datetime,
                "OAuth2Token": OAuth2Token,
                "AppSettings": AppSettings,
                "User": m.User,
                "AppEmailService": AppEmailService,
                "EmailService": EmailService,
            },
        )
        app_config.exception_handlers = {
            ApplicationError: exception_to_http_response,
            ApplicationClientError: exception_to_http_response,
            ValidationError: exception_to_http_response,
            RepositoryError: exception_to_http_response,
            DuplicateKeyError: exception_to_http_response,
        }

        app_config.dependencies.update(
            {
                "current_user": Provide(provide_user, sync_to_thread=False),
                "settings": Provide(provide_app_settings, sync_to_thread=False),
                "app_mailer": Provide(get_mailer_dependency),
            }
        )

        return app_config
