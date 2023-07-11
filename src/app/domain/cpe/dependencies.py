"""CPE Controller Dependencies"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.domain.cpe.models import CPE
from app.domain.cpe.services import CpeService
from app.lib import log

__all__ = ["provides_cpe_service"]


logger = log.get_logger()

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provides_cpe_service(db_session: AsyncSession) -> AsyncGenerator[CpeService, None]:
    """Construct repository and service objects for the request."""
    async with CpeService.new(session=db_session, statement=select(CPE)) as service:
        try:
            yield service
        finally:
            ...
