"""Declarative ``litestar-security`` persistence adapters, resolver, and configuration."""

from app.domain.accounts.security._api_key import (
    APIKeyIdentityResolver,
    SQLAlchemyAPIKeyStore,
    build_api_key_service,
)
from app.domain.accounts.security._backend import SQLAlchemySecurityBackend
from app.domain.accounts.security._config import (
    build_csrf_config,
    build_notification_handler,
    build_security_config,
    build_session_middleware,
    build_session_store,
)
from app.domain.accounts.security._event import AuditSecurityEventSink, sanitize_event_details
from app.domain.accounts.security._mfa import (
    SQLAlchemyMFALoginChallengeService,
    SQLAlchemyMFAService,
    SQLAlchemyStepUpService,
    build_secret_protector,
)
from app.domain.accounts.security._oauth import (
    SQLAlchemyOAuthAccountStore,
    SQLAlchemyOAuthTransactionStore,
    build_oauth_protector,
    deserialize_oauth_tokens,
    oauth_account_aad,
    serialize_oauth_tokens,
)
from app.domain.accounts.security._passkey import SQLAlchemyPasskeyStore
from app.domain.accounts.security._rate_limit import build_rate_limiter
from app.domain.accounts.security._reauth import REAUTHENTICATION_REQUIRED, confirm_authentication
from app.domain.accounts.security._resolver import (
    APPLICATION_ACCESS_REQUIRED,
    TEAM_ROLE_EXPANSION,
    AppAuthorizationResolver,
    ApplicationAccessRouter,
    SelfSubjectPredicate,
    require_application_access,
    requires_self_or_superuser,
    requires_team_role,
)

__all__ = (
    "APPLICATION_ACCESS_REQUIRED",
    "REAUTHENTICATION_REQUIRED",
    "TEAM_ROLE_EXPANSION",
    "APIKeyIdentityResolver",
    "AppAuthorizationResolver",
    "ApplicationAccessRouter",
    "AuditSecurityEventSink",
    "SQLAlchemyAPIKeyStore",
    "SQLAlchemyMFALoginChallengeService",
    "SQLAlchemyMFAService",
    "SQLAlchemyOAuthAccountStore",
    "SQLAlchemyOAuthTransactionStore",
    "SQLAlchemyPasskeyStore",
    "SQLAlchemySecurityBackend",
    "SQLAlchemyStepUpService",
    "SelfSubjectPredicate",
    "build_api_key_service",
    "build_csrf_config",
    "build_notification_handler",
    "build_oauth_protector",
    "build_rate_limiter",
    "build_secret_protector",
    "build_security_config",
    "build_session_middleware",
    "build_session_store",
    "confirm_authentication",
    "deserialize_oauth_tokens",
    "oauth_account_aad",
    "require_application_access",
    "requires_self_or_superuser",
    "requires_team_role",
    "sanitize_event_details",
    "serialize_oauth_tokens",
)
