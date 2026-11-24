"""Account service group sharing one SQLAlchemy AsyncSession."""

from advanced_alchemy.service import ServiceGroup

from app.domain.accounts.services._role import RoleService
from app.domain.accounts.services._user import UserService
from app.domain.accounts.services._user_role import UserRoleService
from app.domain.admin.services._audit import AuditLogService

__all__ = ("AccountServices",)


class AccountServices(ServiceGroup):
    """Coordinated accounts and audit services sharing one ``AsyncSession``."""

    users: UserService
    roles: RoleService
    user_roles: UserRoleService
    audit_logs: AuditLogService
