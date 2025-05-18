# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar.security.jwt import OAuth2Login

if TYPE_CHECKING:
    from click import Group
    from litestar.config.app import AppConfig


T = TypeVar("T")


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

        from uuid import UUID

        from advanced_alchemy.exceptions import RepositoryError
        from litestar.enums import RequestEncodingType
        from litestar.params import Body
        from litestar.security.jwt import Token

        from app import config
        from app import schemas as s
        from app.__metadata__ import __version__
        from app.db import models as m
        from app.lib.exceptions import ApplicationError, exception_to_http_response  # pyright: ignore
        from app.lib.settings import get_settings
        from app.server import events, plugins, routes, security
        from app.services import (
            RoleService,
            TagService,
            TeamInvitationService,
            TeamMemberService,
            TeamService,
            UserOAuthAccountService,
            UserRoleService,
            UserService,
        )

        settings = get_settings()
        self.app_slug = settings.app.slug
        app_config.debug = settings.app.DEBUG
        # openapi
        app_config.openapi_config = OpenAPIConfig(
            title=settings.app.NAME,
            version=__version__,
            components=[security.auth.openapi_components],
            security=[security.auth.security_requirement],
            render_plugins=[ScalarRenderPlugin(version="latest")],
        )
        # jwt auth (updates openapi config)
        app_config = security.auth.on_app_init(app_config)
        # security
        app_config.cors_config = config.cors
        # templates
        app_config.template_config = config.templates
        # plugins
        app_config.plugins.extend(
            [
                plugins.structlog,
                plugins.granian,
                plugins.alchemy,
                plugins.vite,
                plugins.saq,
                plugins.problem_details,
            ],
        )

        # routes
        app_config.route_handlers.extend(
            [
                routes.SystemController,
                routes.AccessController,
                routes.UserController,
                routes.TeamController,
                routes.UserRoleController,
                routes.TeamMemberController,
                routes.TagController,
                routes.WebController,
            ],
        )
        # signatures
        app_config.signature_namespace.update(
            {
                "Token": Token,
                "OAuth2Login": OAuth2Login,
                "RequestEncodingType": RequestEncodingType,
                "Body": Body,
                "m": m,
                "s": s,
                "UUID": UUID,
                "UserService": UserService,
                "RoleService": RoleService,
                "TeamService": TeamService,
                "TeamInvitationService": TeamInvitationService,
                "TeamMemberService": TeamMemberService,
                "TagService": TagService,
                "UserRoleService": UserRoleService,
                "UserOAuthAccountService": UserOAuthAccountService,
            },
        )
        # exception handling
        app_config.exception_handlers = {
            ApplicationError: exception_to_http_response,
            RepositoryError: exception_to_http_response,
        }
        # dependencies
        dependencies = {"current_user": Provide(security.provide_user, sync_to_thread=False)}
        app_config.dependencies.update(dependencies)
        # listeners
        app_config.listeners.extend(
            [events.user.user_created_event_handler, events.team.team_created_event_handler],
        )
        return app_config
