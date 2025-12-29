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

        from datetime import datetime
        from uuid import UUID

        from advanced_alchemy.exceptions import RepositoryError
        from httpx_oauth.oauth2 import OAuth2Token
        from litestar.enums import RequestEncodingType
        from litestar.params import Body
        from litestar.security.jwt import Token

        from app import config
        from app.__metadata__ import __version__
        from app.db import models as m
        from app.domain.accounts import schemas as account_schemas
        from app.domain.accounts import signals as account_signals
        from app.domain.accounts.controllers import (
            AccessController,
            EmailVerificationController,
            MfaChallengeController,
            MfaController,
            OAuthController,
            ProfileController,
            RoleController,
            UserController,
            UserRoleController,
        )
        from app.domain.accounts.guards import auth, provide_user
        from app.domain.accounts.services import (
            EmailVerificationTokenService,
            PasswordResetService,
            RefreshTokenService,
            RoleService,
            UserOAuthAccountService,
            UserRoleService,
            UserService,
        )
        from app.domain.admin import schemas as admin_schemas
        from app.domain.admin.controllers import (
            AdminTeamsController,
            AdminUsersController,
            AuditController,
            DashboardController,
        )
        from app.domain.admin.services import AuditLogService
        from app.domain.system import schemas as system_schemas
        from app.domain.system.controllers import SystemController
        from app.domain.tags import schemas as tag_schemas
        from app.domain.tags.controllers import TagController
        from app.domain.tags.services import TagService
        from app.domain.teams import schemas as team_schemas
        from app.domain.teams import signals as team_signals
        from app.domain.teams.controllers import (
            TeamController,
            TeamInvitationController,
            TeamMemberController,
        )
        from app.domain.teams.services import (
            TeamInvitationService,
            TeamMemberService,
            TeamService,
        )
        from app.lib.exceptions import ApplicationError, exception_to_http_response  # pyright: ignore
        from app.lib.settings import AppSettings, get_settings
        from app.server import plugins

        settings = get_settings()
        self.app_slug = settings.app.slug
        app_config.debug = settings.app.DEBUG
        # openapi
        app_config.openapi_config = OpenAPIConfig(
            title=settings.app.NAME,
            version=__version__,
            components=[auth.openapi_components],
            security=[auth.security_requirement],
            render_plugins=[ScalarRenderPlugin(version="latest")],
        )
        # jwt auth (updates openapi config)
        app_config = auth.on_app_init(app_config)
        # security
        app_config.cors_config = config.cors
        app_config.csrf_config = config.csrf
        # plugins
        app_config.plugins.extend(
            [
                plugins.structlog,
                plugins.granian,
                plugins.alchemy,
                plugins.vite,
                plugins.saq,
                plugins.problem_details,
                plugins.oauth2_provider,
            ],
        )

        # routes
        app_config.route_handlers.extend(
            [
                SystemController,
                AccessController,
                EmailVerificationController,
                MfaChallengeController,
                MfaController,
                OAuthController,
                ProfileController,
                RoleController,
                UserController,
                TeamController,
                TeamInvitationController,
                UserRoleController,
                TeamMemberController,
                TagController,
                # Admin controllers
                AdminTeamsController,
                AdminUsersController,
                AuditController,
                DashboardController,
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
                "UUID": UUID,
                "datetime": datetime,
                "OAuth2Token": OAuth2Token,
                # Services
                "UserService": UserService,
                "EmailVerificationTokenService": EmailVerificationTokenService,
                "PasswordResetService": PasswordResetService,
                "RefreshTokenService": RefreshTokenService,
                "RoleService": RoleService,
                "TeamService": TeamService,
                "TeamInvitationService": TeamInvitationService,
                "TeamMemberService": TeamMemberService,
                "TagService": TagService,
                "UserRoleService": UserRoleService,
                "UserOAuthAccountService": UserOAuthAccountService,
                "AuditLogService": AuditLogService,
                # Settings and models
                "AppSettings": AppSettings,
                "User": m.User,
                # Schemas by domain
                **{k: getattr(account_schemas, k) for k in account_schemas.__all__},
                **{k: getattr(team_schemas, k) for k in team_schemas.__all__},
                **{k: getattr(tag_schemas, k) for k in tag_schemas.__all__},
                **{k: getattr(system_schemas, k) for k in system_schemas.__all__},
                **{k: getattr(admin_schemas, k) for k in admin_schemas.__all__},
            },
        )
        # exception handling
        app_config.exception_handlers = {
            ApplicationError: exception_to_http_response,
            RepositoryError: exception_to_http_response,
        }
        # dependencies
        dependencies = {"current_user": Provide(provide_user, sync_to_thread=False)}
        app_config.dependencies.update(dependencies)
        # listeners
        app_config.listeners.extend(
            [account_signals.user_created_event_handler, team_signals.team_created_event_handler],
        )
        return app_config
