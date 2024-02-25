from __future__ import annotations

from app.db.models import Role, User, UserRole
from app.lib.repository import SQLAlchemyAsyncRepository, SQLAlchemyAsyncSlugRepository


class UserRepository(SQLAlchemyAsyncRepository[User]):
    """User SQLAlchemy Repository."""

    model_type = User


class RoleRepository(SQLAlchemyAsyncSlugRepository[Role]):
    """User SQLAlchemy Repository."""

    model_type = Role


class UserRoleRepository(SQLAlchemyAsyncRepository[UserRole]):
    """User Role SQLAlchemy Repository."""

    model_type = UserRole
