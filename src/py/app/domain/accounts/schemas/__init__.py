"""Account domain schemas for users, auth, OAuth, roles, and password reset."""

from app.domain.accounts.schemas._auth import AccountLogin, AccountRegister, PasswordUpdate, PasswordVerify
from app.domain.accounts.schemas._email_verification import (
    EmailVerificationConfirm,
    EmailVerificationRequest,
    EmailVerificationSent,
    EmailVerificationStatus,
)
from app.domain.accounts.schemas._mfa import (
    LoginMfaChallenge,
    MfaBackupCodes,
    MfaChallenge,
    MfaConfirm,
    MfaDisable,
    MfaSetup,
    MfaStatus,
    MfaVerifyResult,
)
from app.domain.accounts.schemas._oauth import OAuthAccountInfo, OAuthAccountList, OAuthAuthorization
from app.domain.accounts.schemas._password_reset import (
    ForgotPasswordRequest,
    PasswordResetComplete,
    PasswordResetSent,
    ResetPasswordRequest,
    ResetTokenValidation,
    ValidateResetTokenRequest,
)
from app.domain.accounts.schemas._roles import Role, RoleCreate, RoleUpdate, UserRoleAdd, UserRoleRevoke
from app.domain.accounts.schemas._sessions import ActiveSession, SessionList, TokenRefresh
from app.domain.accounts.schemas._user import (
    OauthAccount,
    ProfileUpdate,
    User,
    UserCreate,
    UserRole,
    UserTeam,
    UserUpdate,
)
from app.lib.schema import Message

__all__ = (
    "ActiveSession",
    "AccountLogin",
    "AccountRegister",
    "EmailVerificationConfirm",
    "EmailVerificationRequest",
    "EmailVerificationSent",
    "EmailVerificationStatus",
    "ForgotPasswordRequest",
    "LoginMfaChallenge",
    "Message",
    "MfaBackupCodes",
    "MfaChallenge",
    "MfaConfirm",
    "MfaDisable",
    "MfaSetup",
    "MfaStatus",
    "MfaVerifyResult",
    "OauthAccount",
    "OAuthAccountInfo",
    "OAuthAccountList",
    "OAuthAuthorization",
    "PasswordResetComplete",
    "PasswordResetSent",
    "PasswordUpdate",
    "PasswordVerify",
    "ProfileUpdate",
    "ResetPasswordRequest",
    "ResetTokenValidation",
    "Role",
    "RoleCreate",
    "RoleUpdate",
    "SessionList",
    "TokenRefresh",
    "User",
    "UserCreate",
    "UserRole",
    "UserRoleAdd",
    "UserRoleRevoke",
    "UserTeam",
    "UserUpdate",
    "ValidateResetTokenRequest",
)
