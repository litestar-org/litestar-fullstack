from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import select

from pyspa import models
from pyspa.repositories.base import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepository[models.User]):
    async def get_by_email(
        self, db: "AsyncSession", email: str, options: Optional[List[Any]] = None
    ) -> models.User | None:
        options = options if options else []
        statement = select(self.model).where(self.model.email == email).options(*options)
        return await self.get_one_or_none(db, statement)


user = UserRepository(model=models.User)
