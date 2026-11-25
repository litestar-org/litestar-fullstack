"""Unified ``litestar-security`` configuration factory and session/CSRF middleware builders."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

import structlog
from advanced_alchemy.extensions.litestar.store import SQLAlchemyStore
from litestar.config.csrf import CSRFConfig
from litestar.enums import ScopeType
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar_queues import get_default_service
from litestar_security import (
    MFAConfig,
    PasskeyConfig,
    SecurityConfig,
    SecurityHeadersConfig,
    WebSocketSecurityConfig,
)
from litestar_security.accounts import (
    LocalAuth,
    LocalAuthConfig,
    LocalAuthSecrets,
    NotificationCommand,
    PurposeTokenCodec,
    RecoveryCodePepper,
    RegistrationMode,
    RegistrationPolicy,
    SessionBindingConfig,
    StepUpService,
    forwarded_client_key,
    trusted_client_key,
)
from litestar_security.providers.api_key import APIKeyConfig
from litestar_security.providers.oauth import (
    GitHubOAuthProvider,
    OAuthAccountService,
    OAuthConfig,
    OAuthLifecycleService,
    OAuthLocalAuthTransport,
    OAuthProvider,
    OAuthProviderRegistration,
    OAuthRedirectPolicy,
    OAuthStepUpAuthorizer,
    OAuthTransactionService,
    ProtectedResourceConfig,
    SecretStr,
    StepUpOAuthAuthorizer,
)

from app.db import models as m
from app.domain.accounts.security.api_keys import APIKeyIdentityResolver, SQLAlchemyAPIKeyStore
from app.domain.accounts.security.backend import SQLAlchemySecurityBackend
from app.domain.accounts.security.events import AuditSecurityEventSink
from app.domain.accounts.security.mfa import (
    SQLAlchemyMFALoginChallengeService,
    SQLAlchemyMFAService,
    SQLAlchemyStepUpService,
    build_secret_protector,
)
from app.domain.accounts.security.oauth import (
    SQLAlchemyOAuthAccountStore,
    SQLAlchemyOAuthTransactionStore,
    build_oauth_protector,
)
from app.domain.accounts.security.passkeys import SQLAlchemyPasskeyStore
from app.domain.accounts.security.rate_limit import build_rate_limiter
from app.domain.accounts.security.resolver import AppAuthorizationResolver
from app.lib.secrets import (
    API_KEY_PEPPER_INFO,
    CSRF_SECRET_INFO,
    OAUTH_TRANSACTION_PEPPER_INFO,
    PURPOSE_TOKEN_PEPPER_INFO,
    RECOVERY_CODE_PEPPER_INFO,
    SESSION_BINDING_PEPPER_INFO,
    derive_subkey,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from litestar import Request
    from litestar.middleware import DefineMiddleware
    from litestar_queues import QueueService

    from app.lib.settings import Settings

logger = structlog.get_logger(__name__)

_GITHUB_ISSUER = "https://github.com"

_WILDCARD_PROXY_NETWORKS: tuple[str, ...] = (
    "127.0.0.0/8",
    "10.0.0.0/8",  # NOSONAR - RFC 1918 private range
    "172.16.0.0/12",  # NOSONAR - RFC 1918 private range
    "192.168.0.0/16",  # NOSONAR - RFC 1918 private range
    "100.64.0.0/10",  # NOSONAR - RFC 6598 shared address space
    "169.254.0.0/16",  # NOSONAR - RFC 3927 link-local range
    "::1/128",
    "fc00::/7",
    "fe80::/10",
)
_ACCESS_ROUTE_PREFIX = "/api/access"
_OAUTH_ROUTE_PREFIX = "/api/auth"
_OAUTH_RETURN_PATHS = frozenset({"/", "/home", "/dashboard", "/settings/security", "/auth/github/callback"})
_VERIFICATION_EMAIL_TASK = "email.send_verification"
_RECOVERY_EMAIL_TASK = "email.send_password_reset"

_TEMPLATE_TASK_MAP: dict[str, str] = {
    "local.verify": _VERIFICATION_EMAIL_TASK,
    "local.recovery": _RECOVERY_EMAIL_TASK,
    "verification": _VERIFICATION_EMAIL_TASK,
    "email_verification": _VERIFICATION_EMAIL_TASK,
    "recovery": _RECOVERY_EMAIL_TASK,
    "password_reset": _RECOVERY_EMAIL_TASK,
    "password_reset_confirmation": "email.send_password_reset_confirmation",
}

__all__ = (
    "build_csrf_config",
    "build_notification_handler",
    "build_security_config",
    "build_session_middleware",
    "build_session_store",
)


def build_session_store(alchemy_config: SQLAlchemyAsyncConfig) -> SQLAlchemyStore[SQLAlchemyAsyncConfig]:
    """Build the SQLAlchemy-backed Litestar server-side session store on ``m.AppStore``.

    Returns:
        Configured ``SQLAlchemyStore`` instance for session storage.
    """
    return SQLAlchemyStore(config=alchemy_config, model=m.AppStore, namespace="sessions")


def build_session_middleware(settings: Settings) -> DefineMiddleware:
    """Build Litestar's native server-side session middleware backed by ``SQLAlchemyStore``.

    Returns:
        Configured server-side session middleware definition.
    """
    cookie_secure = _resolve_cookie_secure(settings)
    return ServerSideSessionConfig(
        key="__Host-app-session" if cookie_secure else "app-session",
        max_age=settings.security.SESSION_MAX_AGE,
        secure=cookie_secure,
        httponly=True,
        samesite="lax",
        scopes={ScopeType.HTTP, ScopeType.WEBSOCKET},
        store="sessions",
    ).middleware


def build_csrf_config(settings: Settings) -> CSRFConfig:
    """Build Litestar's native CSRF configuration using an HKDF-derived secret.

    Returns:
        Configured ``CSRFConfig`` instance.
    """
    cookie_secure = _resolve_cookie_secure(settings)
    secret = derive_subkey(settings.app.SECRET_KEY, CSRF_SECRET_INFO, length=32).hex()
    return CSRFConfig(
        secret=secret,
        cookie_name="XSRF-TOKEN",
        header_name="X-XSRF-TOKEN",
        cookie_secure=cookie_secure,
        cookie_httponly=False,
        cookie_samesite="lax",
    )


def build_notification_handler(
    queue_service: QueueService | None = None,
) -> Callable[[NotificationCommand], Awaitable[None]]:
    """Create a ``LocalAuth`` notification callback enqueueing canonical ``email.send_*`` queue tasks.

    Returns:
        Async notification callback accepting a ``NotificationCommand``.
    """

    async def _dispatch_notification(notification: NotificationCommand) -> None:
        task_name = _TEMPLATE_TASK_MAP.get(notification.template)
        if task_name is None:
            logger.warning("Ignoring unmapped security notification template", template=notification.template)
            return
        queues = queue_service if queue_service is not None else get_default_service()
        if queues is None:
            logger.warning("No QueueService available to enqueue security email", task_name=task_name)
            return
        await queues.enqueue(
            task_name,
            queue="emails",
            email=notification.destination,
            token=notification.token,
            token_expires_at=notification.expires_at.isoformat(),
            return_url=notification.return_url,
        )

    return _dispatch_notification


def build_security_config(
    settings: Settings,
    alchemy_config: SQLAlchemyAsyncConfig,
    *,
    queue_service: QueueService | None = None,
) -> SecurityConfig[m.User]:
    """Assemble the complete declarative ``SecurityConfig[m.User]`` for the application.

    Returns:
        Fully configured ``SecurityConfig`` instance.
    """
    backend = SQLAlchemySecurityBackend(
        alchemy_config,
        notification_handler=build_notification_handler(queue_service=queue_service),
    )
    event_sink = AuditSecurityEventSink(alchemy_config)
    step_up_store = SQLAlchemyStepUpService(alchemy_config)
    local_auth = _build_local_auth(settings, alchemy_config, backend, event_sink)
    passkey_config = _build_passkey_config(settings, alchemy_config, backend, event_sink, step_up_store)
    return SecurityConfig(
        local_auth=local_auth,
        mfa=_build_mfa_config(settings, alchemy_config, backend, event_sink, step_up_store),
        passkeys=passkey_config,
        oauth=_build_oauth_config(settings, alchemy_config, local_auth, backend, step_up_store),
        api_key=_build_api_key_config(settings, alchemy_config),
        protected_resource=ProtectedResourceConfig(
            resource=settings.app.URL.rstrip("/"),
            scopes_supported=("read", "write", "mcp"),
        ),
        websocket=_build_websocket_config(settings, backend, passkey_origins=passkey_config.origins),
        headers=SecurityHeadersConfig.hardened(),
        authorization_resolver=AppAuthorizationResolver(),
        exclude=["^/static"],
    )


def _resolve_cookie_secure(settings: Settings) -> bool:
    return bool(settings.security.COOKIE_SECURE or settings.app.COOKIE_SECURE)


def _build_local_auth(
    settings: Settings,
    alchemy_config: SQLAlchemyAsyncConfig,
    backend: SQLAlchemySecurityBackend,
    event_sink: AuditSecurityEventSink,
) -> LocalAuthConfig[m.User]:
    cookie_secure = _resolve_cookie_secure(settings)
    proxy_networks = _trusted_proxy_networks(settings.server.LITESTAR_TRUSTED_PROXIES)
    return LocalAuth.session(
        accounts=backend,
        session_resolver=backend,
        secrets=LocalAuthSecrets(
            purpose_tokens=PurposeTokenCodec(pepper=derive_subkey(settings.app.SECRET_KEY, PURPOSE_TOKEN_PEPPER_INFO)),
        ),
        binding=SessionBindingConfig(
            pepper=derive_subkey(settings.app.SECRET_KEY, SESSION_BINDING_PEPPER_INFO),
            cookie_name="__Host-app-binding" if cookie_secure else "app-binding",
            secure=cookie_secure,
            allow_insecure=not cookie_secure,
            max_age=min(86_400 * 7, settings.security.SESSION_MAX_AGE),
        ),
        registration=RegistrationPolicy(
            mode=RegistrationMode.PUBLIC,
            require_verification=settings.security.REGISTRATION_REQUIRE_VERIFICATION,
        ),
        route_prefix=_ACCESS_ROUTE_PREFIX,
        register_routes=True,
        rate_limiter=build_rate_limiter(alchemy_config),
        events=event_sink,
        client_key=forwarded_client_key(trusted_proxies=proxy_networks) if proxy_networks else trusted_client_key,
    )


def _trusted_proxy_networks(trusted_proxies: list[str]) -> list[str]:
    networks: list[str] = []
    for trusted_proxy in trusted_proxies:
        network = trusted_proxy.strip()
        if network == "*":
            networks.extend(wildcard for wildcard in _WILDCARD_PROXY_NETWORKS if wildcard not in networks)
        elif network and network not in networks:
            networks.append(network)
    return networks


def _build_mfa_config(
    settings: Settings,
    alchemy_config: SQLAlchemyAsyncConfig,
    backend: SQLAlchemySecurityBackend,
    event_sink: AuditSecurityEventSink,
    step_up_store: SQLAlchemyStepUpService,
) -> MFAConfig:
    recovery_code_pepper = derive_subkey(settings.app.SECRET_KEY, RECOVERY_CODE_PEPPER_INFO)
    return MFAConfig(
        store=SQLAlchemyMFAService(alchemy_config),
        secret_protector=build_secret_protector(settings),
        recovery_peppers=(RecoveryCodePepper(key_version="v1", key=recovery_code_pepper),),
        login_methods=backend,
        events=event_sink,
        step_up_store=step_up_store,
        require_at_login="enrolled",
        login_challenge_store=SQLAlchemyMFALoginChallengeService(alchemy_config),
        route_prefix=_ACCESS_ROUTE_PREFIX,
        issuer=settings.app.NAME,
        register_routes=True,
    )


def _build_passkey_config(
    settings: Settings,
    alchemy_config: SQLAlchemyAsyncConfig,
    backend: SQLAlchemySecurityBackend,
    event_sink: AuditSecurityEventSink,
    step_up_store: SQLAlchemyStepUpService,
) -> PasskeyConfig:
    cookie_secure = _resolve_cookie_secure(settings)
    passkey_store = SQLAlchemyPasskeyStore(alchemy_config)
    rp_id = _extract_rp_id(settings.app.URL, settings.security.PASSKEY_RP_ID)
    return PasskeyConfig(
        store=passkey_store,
        challenge_store=passkey_store,
        rp_id=rp_id,
        rp_name=settings.security.PASSKEY_RP_NAME or settings.app.NAME,
        origins=_resolve_passkey_origins(settings, rp_id=rp_id, cookie_secure=cookie_secure),
        allow_insecure_localhost=not cookie_secure,
        login_methods=backend,
        events=event_sink,
        step_up_store=step_up_store,
        route_prefix=_ACCESS_ROUTE_PREFIX,
        register_routes=True,
    )


def _extract_rp_id(app_url: str, configured_rp_id: str) -> str:
    if configured_rp_id and configured_rp_id != "localhost":
        return configured_rp_id
    origin = _normalize_origin(app_url)
    if origin is not None:
        hostname = urlparse(origin).hostname
        if hostname:
            return hostname
    return configured_rp_id or "localhost"


def _resolve_passkey_origins(settings: Settings, *, rp_id: str, cookie_secure: bool) -> tuple[str, ...]:
    origins: list[str] = []
    for url in (settings.app.URL, *settings.security.PASSKEY_ORIGINS):
        origin = _normalize_origin(url)
        if origin is None:
            continue
        parsed = urlparse(origin)
        if cookie_secure and parsed.scheme != "https":
            continue
        if parsed.hostname != rp_id and not (parsed.hostname or "").endswith(f".{rp_id}"):
            continue
        if origin not in origins:
            origins.append(origin)
    if not origins:
        scheme = "https" if cookie_secure else "http"
        origins.append(f"{scheme}://{rp_id}")
    return tuple(origins)


def _normalize_origin(url: str) -> str | None:
    candidate = url.strip().rstrip("/")
    if not candidate:
        return None
    try:
        parsed = urlparse(candidate)
        _ = parsed.port
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _build_oauth_config(
    settings: Settings,
    alchemy_config: SQLAlchemyAsyncConfig,
    local_auth: LocalAuthConfig[m.User],
    backend: SQLAlchemySecurityBackend,
    step_up_store: SQLAlchemyStepUpService,
) -> OAuthConfig | None:
    if not settings.app.github_oauth_enabled:
        return None
    github = _github_registration(settings)
    protector = build_oauth_protector(settings)
    transactions = OAuthTransactionService(
        store=SQLAlchemyOAuthTransactionStore(alchemy_config, protector),
        pepper=derive_subkey(settings.app.SECRET_KEY, OAUTH_TRANSACTION_PEPPER_INFO),
        redirects=OAuthRedirectPolicy(
            callback_uris={"github": frozenset({github.redirect_uri})},
            return_to=_OAUTH_RETURN_PATHS,
            allow_insecure_localhost=not _resolve_cookie_secure(settings),
        ),
        lifetime=timedelta(minutes=10),
    )
    lifecycle = OAuthLifecycleService(
        registrations=(github,),
        transactions=transactions,
        accounts=OAuthAccountService(
            store=SQLAlchemyOAuthAccountStore(alchemy_config, protector),
            provision_unknown=True,
        ),
        local=OAuthLocalAuthTransport(
            local_auth_service=local_auth.local_auth_service,  # type: ignore[arg-type]
        ),
        step_up=cast("OAuthStepUpAuthorizer", _build_oauth_step_up_authorizer(local_auth, backend, step_up_store)),
    )
    return OAuthConfig(oauth_service=lifecycle, route_prefix=_OAUTH_ROUTE_PREFIX, register_routes=True)


def _github_registration(settings: Settings) -> OAuthProviderRegistration:
    provider = GitHubOAuthProvider(
        client_id=settings.app.GITHUB_OAUTH2_CLIENT_ID,
        client_secret=SecretStr(settings.app.GITHUB_OAUTH2_CLIENT_SECRET),
    )
    return OAuthProviderRegistration(
        provider=cast("OAuthProvider", provider),
        redirect_uri=f"{settings.app.URL.rstrip('/')}{_OAUTH_ROUTE_PREFIX}/oauth/github/callback",
        default_scopes=frozenset({"user:email", "read:user"}),
        expected_issuer=_GITHUB_ISSUER,
        retain_tokens=True,
    )


def _build_oauth_step_up_authorizer(
    local_auth: LocalAuthConfig[m.User],
    backend: SQLAlchemySecurityBackend,
    step_up_store: SQLAlchemyStepUpService,
) -> StepUpOAuthAuthorizer:
    session_auth = local_auth.session_auth

    def current_session_id(request: Request[Any, Any, Any]) -> str | None:
        if session_auth is None:
            return None
        authentication = session_auth.current_authentication(request)
        return authentication.session_id if authentication is not None else None

    return StepUpOAuthAuthorizer.from_step_up_service(
        StepUpService(step_up_store),
        epochs=backend,
        session_binding=current_session_id,
    )


def _build_api_key_config(settings: Settings, alchemy_config: SQLAlchemyAsyncConfig) -> APIKeyConfig:
    api_key_store = SQLAlchemyAPIKeyStore(alchemy_config)
    return APIKeyConfig(
        store=api_key_store,
        pepper=derive_subkey(settings.app.SECRET_KEY, API_KEY_PEPPER_INFO),
        identity_resolver=APIKeyIdentityResolver(alchemy_config),
        usage_sink=api_key_store,
        accept_authorization_bearer=True,
    )


def _build_websocket_config(
    settings: Settings,
    backend: SQLAlchemySecurityBackend,
    *,
    passkey_origins: Sequence[str],
) -> WebSocketSecurityConfig:
    cors_origins = (_normalize_origin(url) for url in settings.app.ALLOWED_CORS_ORIGINS)
    return WebSocketSecurityConfig(
        allowed_origins=frozenset({*passkey_origins, *(origin for origin in cors_origins if origin is not None)}),
        current_security_epoch=backend.current_epoch,
    )
