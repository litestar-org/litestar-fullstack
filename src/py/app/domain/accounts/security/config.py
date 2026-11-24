"""Unified ``litestar-security`` configuration factory and session/CSRF middleware builders."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

import structlog
from litestar.config.csrf import CSRFConfig
from litestar.enums import ScopeType
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar_queues import get_default_service
from litestar_security import (
    MFAConfig,
    PasskeyConfig,
    SecurityConfig,
    SecurityHeadersConfig,
)
from litestar_security.accounts import (
    LocalAuth,
    LocalAuthSecrets,
    NotificationCommand,
    PurposeTokenCodec,
    RecoveryCodePepper,
    RegistrationMode,
    RegistrationPolicy,
    SessionBindingConfig,
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
    OAuthTransactionService,
    ProtectedResourceConfig,
    SecretStr,
)

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
    PURPOSE_TOKEN_PEPPER_INFO,
    RECOVERY_CODE_PEPPER_INFO,
    SESSION_BINDING_PEPPER_INFO,
    SESSION_COOKIE_SECRET_INFO,
    derive_subkey,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig
    from litestar.middleware import DefineMiddleware
    from litestar_queues import QueueService

    from app.db import models as m
    from app.lib.settings import Settings

logger = structlog.get_logger(__name__)

_TEMPLATE_TASK_MAP: dict[str, str] = {
    "verification": "email.send_verification",
    "email_verification": "email.send_verification",
    "recovery": "email.send_password_reset",
    "password_reset": "email.send_password_reset",
    "password_reset_confirmation": "email.send_password_reset_confirmation",
}

__all__ = (
    "build_csrf_config",
    "build_notification_handler",
    "build_security_config",
    "build_session_middleware",
)


def _normalize_origin(raw: str) -> str | None:
    candidate = raw.strip().rstrip("/")
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


def _extract_rp_id(app_url: str, configured_rp_id: str) -> str:
    if configured_rp_id and configured_rp_id != "localhost":
        return configured_rp_id
    normalized = _normalize_origin(app_url)
    if normalized is not None:
        hostname = urlparse(normalized).hostname
        if hostname:
            return hostname
    return configured_rp_id or "localhost"


def _resolve_passkey_origins(settings: Settings, *, rp_id: str, cookie_secure: bool) -> tuple[str, ...]:
    candidates: list[str] = []
    for raw in (settings.app.URL, *settings.security.PASSKEY_ORIGINS):
        origin = _normalize_origin(raw)
        if origin is None:
            continue
        parsed = urlparse(origin)
        if cookie_secure and parsed.scheme != "https":
            continue
        if parsed.hostname != rp_id and not (parsed.hostname or "").endswith(f".{rp_id}"):
            continue
        if origin not in candidates:
            candidates.append(origin)
    if not candidates:
        scheme = "https" if cookie_secure else "http"
        candidates.append(f"{scheme}://{rp_id}")
    return tuple(candidates)


def _resolve_cookie_secure(settings: Settings) -> bool:
    return bool(settings.security.COOKIE_SECURE or settings.app.COOKIE_SECURE)


def build_session_middleware(settings: Settings) -> DefineMiddleware:
    """Build Litestar's native encrypted cookie session middleware using an HKDF-derived 32-byte key."""
    cookie_secure = _resolve_cookie_secure(settings)
    secret = derive_subkey(settings.app.SECRET_KEY, SESSION_COOKIE_SECRET_INFO, length=32)
    return CookieBackendConfig(
        secret=secret,
        key="__Host-app-session" if cookie_secure else "app-session",
        max_age=settings.security.SESSION_MAX_AGE,
        secure=cookie_secure,
        httponly=True,
        samesite="lax",
        scopes={ScopeType.HTTP, ScopeType.WEBSOCKET},
    ).middleware


def build_csrf_config(settings: Settings) -> CSRFConfig:
    """Build Litestar's native CSRF configuration using an HKDF-derived secret."""
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
    """Create a ``LocalAuth`` notification callback enqueueing canonical ``email.send_*`` queue tasks."""

    async def _dispatch_notification(notification: NotificationCommand) -> None:
        task_name = _TEMPLATE_TASK_MAP.get(notification.template)
        if task_name is None:
            logger.warning("Ignoring unmapped security notification template", template=notification.template)
            return
        service = queue_service if queue_service is not None else get_default_service()
        if service is None:
            logger.warning("No QueueService available to enqueue security email", task_name=task_name)
            return
        payload: dict[str, Any] = {
            "email": notification.destination,
            "token": notification.token,
            "expires_at": notification.expires_at.isoformat(),
            "return_url": notification.return_url,
        }
        await service.enqueue(task_name, kwargs=payload, queue="emails")

    return _dispatch_notification


def _build_oauth_config(
    settings: Settings,
    alchemy_config: SQLAlchemyAsyncConfig,
    local_auth_config: Any,
) -> OAuthConfig | None:
    if not (settings.app.github_oauth_enabled or settings.app.google_oauth_enabled):
        return None

    base_url = settings.app.URL.rstrip("/")
    cookie_secure = _resolve_cookie_secure(settings)
    registrations: list[OAuthProviderRegistration] = []
    callback_uris: dict[str, frozenset[str]] = {}

    if settings.app.github_oauth_enabled:
        github_callback = f"{base_url}/api/auth/oauth/github/callback"
        github_provider = GitHubOAuthProvider(
            client_id=settings.app.GITHUB_OAUTH2_CLIENT_ID,
            client_secret=SecretStr(settings.app.GITHUB_OAUTH2_CLIENT_SECRET),
        )
        registrations.append(
            OAuthProviderRegistration(
                provider=cast("OAuthProvider", github_provider),
                redirect_uri=github_callback,
                default_scopes=frozenset({"user:email", "read:user"}),
                retain_tokens=True,
            )
        )
        callback_uris["github"] = frozenset({github_callback})

    if not registrations:
        return None

    protector = build_oauth_protector(settings)
    tx_store = SQLAlchemyOAuthTransactionStore(alchemy_config, protector)
    account_store = SQLAlchemyOAuthAccountStore(alchemy_config, protector)
    tx_pepper = derive_subkey(settings.app.SECRET_KEY, PURPOSE_TOKEN_PEPPER_INFO)
    redirects = OAuthRedirectPolicy(
        callback_uris=callback_uris,
        return_to=frozenset({"/", "/dashboard", "/auth/github/callback", "/auth/google/callback"}),
        allow_insecure_localhost=not cookie_secure,
    )
    tx_service = OAuthTransactionService(
        store=tx_store,
        pepper=tx_pepper,
        redirects=redirects,
        lifetime=timedelta(minutes=10),
    )
    account_service = OAuthAccountService(store=account_store, provision_unknown=True)
    local_transport = OAuthLocalAuthTransport(local_auth_service=local_auth_config.local_auth_service)
    lifecycle = OAuthLifecycleService(
        registrations=tuple(registrations),
        transactions=tx_service,
        accounts=account_service,
        local=local_transport,
    )
    return OAuthConfig(
        oauth_service=lifecycle,
        route_prefix="/api/auth/oauth",
        register_routes=True,
    )


def build_security_config(
    settings: Settings,
    alchemy_config: SQLAlchemyAsyncConfig,
    *,
    queue_service: QueueService | None = None,
) -> SecurityConfig[m.User]:
    """Assemble the complete declarative ``SecurityConfig[m.User]`` for the application."""
    cookie_secure = _resolve_cookie_secure(settings)
    master = settings.app.SECRET_KEY

    purpose_token_pepper = derive_subkey(master, PURPOSE_TOKEN_PEPPER_INFO)
    recovery_code_pepper = derive_subkey(master, RECOVERY_CODE_PEPPER_INFO)
    binding_pepper = derive_subkey(master, SESSION_BINDING_PEPPER_INFO)
    api_key_pepper = derive_subkey(master, API_KEY_PEPPER_INFO)

    backend = SQLAlchemySecurityBackend(
        alchemy_config,
        notification_handler=build_notification_handler(queue_service=queue_service),
    )
    event_sink = AuditSecurityEventSink(alchemy_config)
    rate_limiter = build_rate_limiter(alchemy_config)

    client_key = (
        forwarded_client_key(trusted_proxies=settings.server.LITESTAR_TRUSTED_PROXIES)
        if settings.server.LITESTAR_TRUSTED_PROXIES
        else trusted_client_key
    )

    local_auth = LocalAuth.session(
        accounts=backend,
        session_resolver=backend,
        secrets=LocalAuthSecrets(purpose_tokens=PurposeTokenCodec(pepper=purpose_token_pepper)),
        binding=SessionBindingConfig(
            pepper=binding_pepper,
            cookie_name="__Host-app-binding" if cookie_secure else "app-binding",
            secure=cookie_secure,
            allow_insecure=not cookie_secure,
            max_age=min(86_400 * 7, settings.security.SESSION_MAX_AGE),
        ),
        registration=RegistrationPolicy(
            mode=RegistrationMode.PUBLIC,
            require_verification=True,
        ),
        route_prefix="/api/access",
        register_routes=True,
        rate_limiter=rate_limiter,
        events=event_sink,
        client_key=client_key,
    )

    mfa_store = SQLAlchemyMFAService(alchemy_config)
    step_up_store = SQLAlchemyStepUpService(alchemy_config)
    login_challenge_store = SQLAlchemyMFALoginChallengeService(alchemy_config)
    mfa_config = MFAConfig(
        store=mfa_store,
        secret_protector=build_secret_protector(settings),
        recovery_peppers=(RecoveryCodePepper(key_version="v1", key=recovery_code_pepper),),
        login_methods=backend,
        events=event_sink,
        step_up_store=step_up_store,
        require_at_login="enrolled",
        login_challenge_store=login_challenge_store,
        route_prefix="/api/access",
        issuer=settings.app.NAME,
        register_routes=True,
    )

    passkey_store = SQLAlchemyPasskeyStore(alchemy_config)
    rp_id = _extract_rp_id(settings.app.URL, settings.security.PASSKEY_RP_ID)
    origins = _resolve_passkey_origins(settings, rp_id=rp_id, cookie_secure=cookie_secure)
    passkey_config = PasskeyConfig(
        store=passkey_store,
        challenge_store=passkey_store,
        rp_id=rp_id,
        rp_name=settings.security.PASSKEY_RP_NAME or settings.app.NAME,
        origins=origins,
        allow_insecure_localhost=not cookie_secure,
        login_methods=backend,
        events=event_sink,
        step_up_store=step_up_store,
        route_prefix="/api/access",
        register_routes=True,
    )

    oauth_config = _build_oauth_config(settings, alchemy_config, local_auth)

    api_key_store = SQLAlchemyAPIKeyStore(alchemy_config)
    api_key_config = APIKeyConfig(
        store=api_key_store,
        pepper=api_key_pepper,
        identity_resolver=APIKeyIdentityResolver(alchemy_config),
        usage_sink=api_key_store,
        accept_authorization_bearer=True,
    )

    protected_resource = ProtectedResourceConfig(
        resource=settings.app.URL.rstrip("/"),
        scopes_supported=("read", "write", "mcp"),
    )

    return SecurityConfig(
        local_auth=local_auth,
        mfa=mfa_config,
        passkeys=passkey_config,
        oauth=oauth_config,
        api_key=api_key_config,
        protected_resource=protected_resource,
        headers=SecurityHeadersConfig.hardened(),
        authorization_resolver=AppAuthorizationResolver(),
        exclude=["^/static"],
    )
