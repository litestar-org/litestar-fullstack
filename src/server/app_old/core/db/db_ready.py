from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


async def is_available(engine: "AsyncEngine") -> bool:
    """
    Checks for database connectivity.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # pylint: disable=broad-except
        return False
    else:
        return True
