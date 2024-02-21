from __future__ import annotations

from typing import TYPE_CHECKING

import uvicorn
from advanced_alchemy.base import create_registry
from litestar import Controller, Litestar, get, post
from litestar.exceptions import HTTPException
from litestar.openapi import OpenAPIConfig
from litestar.plugins.sqlalchemy import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyDTO,
    SQLAlchemyPlugin,
)
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# from advanced_alchemy.extensions.litestar.plugins.init.config.asyncio import autocommit_before_send_handler  # noqa: ERA001

DATABASE_URL = "sqlite+aiosqlite:///test.db"


class Base(DeclarativeBase):
    """Base for SQLAlchemy declarative models with BigInt primary keys."""

    registry = create_registry()


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    location_name: Mapped[str] = mapped_column(nullable=False)


class LocationsController(Controller):
    LocationDTO = SQLAlchemyDTO[Location]
    path = "/locations"
    dto = LocationDTO
    return_dto = LocationDTO

    @post(path="/create", description="Create a new location")
    async def create_location(self, data: Location, session: AsyncSession) -> Location:
        session.add(data)
        await session.commit()

        return data

    @get(path="/get/{location_id:str}", description="Get a location by id")
    async def get_location(self, location_id: str, session: AsyncSession) -> Location:
        query = select(Location).where(Location.id == location_id)
        r = await session.execute(query)
        if r := r.scalar_one_or_none():  # type: ignore[assignment]
            return r
        raise HTTPException(status_code=404, detail="Location not found")


alchemy = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    # before_send_handler=autocommit_before_send_handler,  # noqa: ERA001
    session_dependency_key="session",
    session_config=AsyncSessionConfig(expire_on_commit=False),
    metadata=Base.metadata,
)


async def on_startup() -> None:
    """Initializes the database."""
    async with alchemy.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def app() -> Litestar:
    routes = [LocationsController]
    return Litestar(
        route_handlers=routes,
        on_startup=[on_startup],
        plugins=[
            SQLAlchemyPlugin(
                config=alchemy,
            ),
        ],
        openapi_config=OpenAPIConfig(title="Serve API", version="0.0.1"),
        debug=True,
    )


async with alchemy.get_session() as db_session:
    await db_session.execute(text("select for from bar"))

# Run with uvicorn
if __name__ == "__main__":
    uvicorn.run("mcve:app", host="0.0.0.0", port=8080, reload=True, factory=True)
