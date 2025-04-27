from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import get
from litestar.testing import AsyncTestClient

if TYPE_CHECKING:
    from litestar import Litestar
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


async def test_db_session_dependency(app: Litestar, engine: AsyncEngine) -> None:
    """Test that handlers receive session attached to patched engine.

    Args:
        app: The test Litestar instance
        engine: The patched SQLAlchemy engine instance.
    """

    @get("/db-session-test", opt={"exclude_from_auth": True})
    async def db_session_dependency_patched(db_session: AsyncSession) -> dict[str, str]:
        return {"result": f"{db_session.bind is engine = }"}

    app.register(db_session_dependency_patched)
    # can't use test client as it always starts its own event loop
    async with AsyncTestClient(app) as client:
        response = await client.get("/db-session-test")
        assert response.json()["result"] == "db_session.bind is engine = True"
