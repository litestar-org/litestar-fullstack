from app.server.routes.access import AccessController
from app.server.routes.email_verification import EmailVerificationController
from app.server.routes.oauth import OAuthController
from app.server.routes.profile import ProfileController
from app.server.routes.roles import RoleController
from app.server.routes.system import SystemController
from app.server.routes.tag import TagController
from app.server.routes.team import TeamController
from app.server.routes.team_invitation import TeamInvitationController
from app.server.routes.team_member import TeamMemberController
from app.server.routes.user import UserController
from app.server.routes.user_role import UserRoleController
from app.server.routes.web import WebController

__all__ = (
    "AccessController",
    "EmailVerificationController",
    "OAuthController",
    "ProfileController",
    "RoleController",
    "SystemController",
    "TagController",
    "TeamController",
    "TeamInvitationController",
    "TeamMemberController",
    "UserController",
    "UserRoleController",
    "WebController",
)
