from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from litestar.events import listener

from app.config import alchemy
from app.server import deps

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()


@listener("user_created")
async def user_created_event_handler(user_id: UUID) -> None:
    """Executes when a new user is created.

    Args:
        user_id: The primary key of the user that was created.
    """
    await logger.ainfo("Running post signup flow.")
    async with alchemy.get_session() as db_session:
        service = await anext(deps.provide_users_service(db_session))
        obj = await service.get_one_or_none(id=user_id)
        if obj is None:
            await logger.aerror("Could not locate the specified user", id=user_id)
        else:
            await logger.ainfo("Found user", **obj.to_dict(exclude={"hashed_password"}))
