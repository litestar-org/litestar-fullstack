from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import noload

from app.lib.service import RepositoryService

from .models import User

if TYPE_CHECKING:
    pass

__all__ = ["UserService"]


class UserService(RepositoryService[User]):
    """User Service."""

    async def exists(self, username: str) -> bool:
        """Check if the user exist.

        Args:
            db_session (AsyncSession): _description_
            username (str): username to find.

        Returns:
            bool: True if the user is found.
        """
        statement = select(User.id).where(User.email == username).options(noload("*"))
        user_exists = await self.repository.count(statement)
        return bool(user_exists is not None and user_exists > 0)
