"""Accounts domain services."""

from __future__ import annotations

from app.domain.accounts.services._api_key import APIKeyRecordService
from app.domain.accounts.services._group import (
    AccountSecurityServices,
    AccountServices,
    MFAServices,
    OAuthServices,
    PasskeyServices,
)
from app.domain.accounts.services._mfa import (
    MFAFactorService,
    MFALoginChallengeService,
    MFARecoveryCodeService,
    StepUpGrantService,
)
from app.domain.accounts.services._oauth import OAuthAccountService, OAuthTransactionService
from app.domain.accounts.services._passkey import PasskeyChallengeService, PasskeyService
from app.domain.accounts.services._role import RoleService
from app.domain.accounts.services._session import (
    LoginMethodService,
    PurposeTokenService,
    TokenRejection,
    UserSessionService,
)
from app.domain.accounts.services._statements import is_constraint_violation
from app.domain.accounts.services._user import PASSWORD_POLICY, UserService
from app.domain.accounts.services._user_role import UserRoleService

__all__ = (
    "PASSWORD_POLICY",
    "APIKeyRecordService",
    "AccountSecurityServices",
    "AccountServices",
    "LoginMethodService",
    "MFAFactorService",
    "MFALoginChallengeService",
    "MFARecoveryCodeService",
    "MFAServices",
    "OAuthAccountService",
    "OAuthServices",
    "OAuthTransactionService",
    "PasskeyChallengeService",
    "PasskeyService",
    "PasskeyServices",
    "PurposeTokenService",
    "RoleService",
    "StepUpGrantService",
    "TokenRejection",
    "UserRoleService",
    "UserService",
    "UserSessionService",
    "is_constraint_violation",
)
