"""Account domain controllers."""

from app.domain.accounts.controllers._access import AccessController
from app.domain.accounts.controllers._email_verification import EmailVerificationController
from app.domain.accounts.controllers._oauth import OAuthController
from app.domain.accounts.controllers._profile import ProfileController
from app.domain.accounts.controllers._roles import RoleController
from app.domain.accounts.controllers._user import UserController
from app.domain.accounts.controllers._user_role import UserRoleController

__all__ = (
    "AccessController",
    "EmailVerificationController",
    "OAuthController",
    "ProfileController",
    "RoleController",
    "UserController",
    "UserRoleController",
)
