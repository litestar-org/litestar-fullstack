"""Declarative ``litestar-security`` persistence adapters, resolver, and configuration."""

from app.domain.accounts.security.api_keys import (
    APIKeyIdentityResolver,
    SQLAlchemyAPIKeyStore,
    build_api_key_service,
)
from app.domain.accounts.security.backend import SQLAlchemySecurityBackend
from app.domain.accounts.security.config import (
    build_csrf_config,
    build_notification_handler,
    build_security_config,
    build_session_middleware,
    build_session_store,
)
from app.domain.accounts.security.events import AuditSecurityEventSink, sanitize_event_details
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
from app.domain.accounts.security.resolver import (
    TEAM_ROLE_EXPANSION,
    AppAuthorizationResolver,
    SelfSubjectPredicate,
    requires_self_or_superuser,
    requires_team_role,
)

__all__ = (
    "TEAM_ROLE_EXPANSION",
    "APIKeyIdentityResolver",
    "AppAuthorizationResolver",
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
    "requires_self_or_superuser",
    "requires_team_role",
    "sanitize_event_details",
)
