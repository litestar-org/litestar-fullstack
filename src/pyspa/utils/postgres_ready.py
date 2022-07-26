import asyncio
import sys

from app.core.db import engine
from sqlalchemy import text


async def c() -> None:
    """
    Checks for database connectivity.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:  # pylint: disable=broad-except
        print(f"Waiting for Postgres: {e}")  # noqa: T201
        sys.exit(-1)
    else:
        print("Postgres OK!")  # noqa: T201


def main() -> None:
    """Entrypoint"""
    asyncio.run(c())
