from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.models import Tag
from app.domain.tags.services import TagService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["provide_tags_service"]


async def provide_tags_service(
    db_session: AsyncSession | None = None,
) -> AsyncGenerator[TagService, None]:
    """Provide Tags service.

    Args:
        db_session (AsyncSession | None, optional): current database session. Defaults to None.

    Returns:
        TagService: An Tags service object
    """
    async with TagService.new(session=db_session, statement=select(Tag)) as service:
        yield service
