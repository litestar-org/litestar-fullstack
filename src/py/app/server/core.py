# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, cast

from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar.security.jwt import OAuth2Login

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from datetime import datetime
    from uuid import UUID

    from click import Group
    from httpx_oauth.oauth2 import OAuth2Token
    from litestar import Request
    from litestar.config.app import AppConfig
    from litestar.enums import RequestEncodingType
    from litestar.security.jwt import Token
    from litestar_email import EmailService

    from app.domain.accounts.services import (
        EmailVerificationTokenService,
        PasswordResetService,
        RefreshTokenService,
        RoleService,
        UserOAuthAccountService,
        UserRoleService,
        UserService,
    )
    from app.domain.admin.services import AuditLogService
    from app.domain.tags.services import TagService
    from app.domain.teams.services import TeamInvitationService, TeamMemberService, TeamService
    from app.lib.email import AppEmailService
    from app.lib.settings import AppSettings, Settings

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

        from advanced_alchemy.exceptions import DuplicateKeyError, RepositoryError
        from httpx_oauth.oauth2 import OAuth2Token
        from litestar.enums import RequestEncodingType
        from litestar.params import Body
        from litestar.security.jwt import Token
        from litestar_email import EmailService

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
            OAuthAccountController,
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
        from app.lib.email import AppEmailService
        from app.lib.exceptions import (
            ApplicationClientError,
            ApplicationError,
            exception_to_http_response,
        )
        from app.lib.settings import AppSettings, get_settings, provide_app_settings
        from app.server import plugins

        settings = get_settings()
        self.app_slug = settings.app.slug
        app_config.debug = settings.app.DEBUG
        app_config = self._configure_openapi(app_config, settings=settings, version=__version__, auth=auth)
        app_config.cors_config = config.cors
        self._configure_plugins(app_config, plugins=plugins)
        self._configure_routes(
            app_config,
            controllers=[
                SystemController,
                AccessController,
                EmailVerificationController,
                MfaChallengeController,
                MfaController,
                OAuthController,
                OAuthAccountController,
                ProfileController,
                RoleController,
                UserController,
                TeamController,
                TeamInvitationController,
                UserRoleController,
                TeamMemberController,
                TagController,
                AdminTeamsController,
                AdminUsersController,
                AuditController,
                DashboardController,
            ],
        )
        self._configure_signature_namespace(
            app_config,
            token=Token,
            oauth2_login=OAuth2Login,
            request_encoding_type=RequestEncodingType,
            body=Body,
            models=m,
            uuid=UUID,
            datetime=datetime,
            oauth2_token=OAuth2Token,
            user_service=UserService,
            email_verification_service=EmailVerificationTokenService,
            password_reset_service=PasswordResetService,
            refresh_token_service=RefreshTokenService,
            role_service=RoleService,
            team_service=TeamService,
            team_invitation_service=TeamInvitationService,
            team_member_service=TeamMemberService,
            tag_service=TagService,
            user_role_service=UserRoleService,
            user_oauth_service=UserOAuthAccountService,
            audit_log_service=AuditLogService,
            app_settings=AppSettings,
            app_email_service=AppEmailService,
            email_service=EmailService,
            account_schemas=account_schemas,
            team_schemas=team_schemas,
            tag_schemas=tag_schemas,
            system_schemas=system_schemas,
            admin_schemas=admin_schemas,
        )
        self._configure_exception_handlers(
            app_config,
            exception_to_http_response=exception_to_http_response,
            application_error=ApplicationError,
            application_client_error=ApplicationClientError,
            repository_error=RepositoryError,
            duplicate_key_error=DuplicateKeyError,
        )
        self._configure_dependencies(app_config, provide_user=provide_user, provide_app_settings=provide_app_settings)
        self._configure_listeners(app_config, account_signals=account_signals, team_signals=team_signals)
        return app_config

    def _configure_openapi(
        self,
        app_config: AppConfig,
        *,
        settings: Settings,
        version: str,
        auth: Any,
    ) -> AppConfig:
        app_config.openapi_config = OpenAPIConfig(
            title=settings.app.NAME,
            version=version,
            components=[auth.openapi_components],
            security=[auth.security_requirement],
            render_plugins=[ScalarRenderPlugin(version="latest")],
        )
        return cast("AppConfig", auth.on_app_init(app_config))

    def _configure_plugins(self, app_config: AppConfig, *, plugins: Any) -> None:
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
            ],
        )

    def _configure_routes(self, app_config: AppConfig, *, controllers: list[type]) -> None:
        app_config.route_handlers.extend(controllers)

    def _configure_signature_namespace(
        self,
        app_config: AppConfig,
        *,
        token: type[Token],
        oauth2_login: type[OAuth2Login],
        request_encoding_type: type[RequestEncodingType],
        body: Callable[..., Any],
        models: Any,
        uuid: type[UUID],
        datetime: type[datetime],
        oauth2_token: type[OAuth2Token],
        user_service: type[UserService],
        email_verification_service: type[EmailVerificationTokenService],
        password_reset_service: type[PasswordResetService],
        refresh_token_service: type[RefreshTokenService],
        role_service: type[RoleService],
        team_service: type[TeamService],
        team_invitation_service: type[TeamInvitationService],
        team_member_service: type[TeamMemberService],
        tag_service: type[TagService],
        user_role_service: type[UserRoleService],
        user_oauth_service: type[UserOAuthAccountService],
        audit_log_service: type[AuditLogService],
        app_settings: type[AppSettings],
        app_email_service: type[AppEmailService],
        email_service: type[EmailService],
        account_schemas: Any,
        team_schemas: Any,
        tag_schemas: Any,
        system_schemas: Any,
        admin_schemas: Any,
    ) -> None:
        app_config.signature_namespace.update(
            {
                "Token": token,
                "OAuth2Login": oauth2_login,
                "RequestEncodingType": request_encoding_type,
                "Body": body,
                "m": models,
                "UUID": uuid,
                "datetime": datetime,
                "OAuth2Token": oauth2_token,
                "UserService": user_service,
                "EmailVerificationTokenService": email_verification_service,
                "PasswordResetService": password_reset_service,
                "RefreshTokenService": refresh_token_service,
                "RoleService": role_service,
                "TeamService": team_service,
                "TeamInvitationService": team_invitation_service,
                "TeamMemberService": team_member_service,
                "TagService": tag_service,
                "UserRoleService": user_role_service,
                "UserOAuthAccountService": user_oauth_service,
                "AuditLogService": audit_log_service,
                "AppSettings": app_settings,
                "User": models.User,
                "AppEmailService": app_email_service,
                "EmailService": email_service,
                **{k: getattr(account_schemas, k) for k in account_schemas.__all__},
                **{k: getattr(team_schemas, k) for k in team_schemas.__all__},
                **{k: getattr(tag_schemas, k) for k in tag_schemas.__all__},
                **{k: getattr(system_schemas, k) for k in system_schemas.__all__},
                **{k: getattr(admin_schemas, k) for k in admin_schemas.__all__},
            },
        )

    def _configure_exception_handlers(
        self,
        app_config: AppConfig,
        *,
        exception_to_http_response: Any,
        application_error: type[Exception],
        application_client_error: type[Exception],
        repository_error: type[Exception],
        duplicate_key_error: type[Exception],
    ) -> None:
        app_config.exception_handlers = {
            application_error: exception_to_http_response,
            application_client_error: exception_to_http_response,
            repository_error: exception_to_http_response,
            duplicate_key_error: exception_to_http_response,
        }

    def _configure_dependencies(
        self,
        app_config: AppConfig,
        *,
        provide_user: Any,
        provide_app_settings: Any,
    ) -> None:
        from app.lib.email import AppEmailService

        async def provide_app_email_service(request: Request[Any, Any, Any]) -> AsyncGenerator[AppEmailService, None]:
            email_config = request.app.state.mailer
            async with email_config.provide_service() as mailer:
                yield AppEmailService(mailer=mailer)

        dependencies = {
            "current_user": Provide(provide_user, sync_to_thread=False),
            "settings": Provide(provide_app_settings, sync_to_thread=False),
            # Note: sync_to_thread is not used for generators - they're managed by the event loop
            "app_email_service": Provide(provide_app_email_service),
        }
        app_config.dependencies.update(dependencies)

    def _configure_listeners(
        self,
        app_config: AppConfig,
        *,
        account_signals: Any,
        team_signals: Any,
    ) -> None:
        app_config.listeners.extend(
            [account_signals.user_created_event_handler, team_signals.team_created_event_handler],
        )
