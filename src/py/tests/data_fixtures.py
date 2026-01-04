from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from httpx import AsyncClient
    from litestar import Litestar
    from pytest import MonkeyPatch

    from app.db.models import Team, User

pytestmark = pytest.mark.anyio


@pytest.fixture(name="app")
def fx_app(pytestconfig: pytest.Config, monkeypatch: MonkeyPatch) -> Litestar:
    """App fixture.

    Returns:
        An application instance, configured via plugin.
    """
    from app.server.asgi import create_app

    return create_app()


@pytest.fixture(name="raw_users")
def fx_raw_users() -> list[User | dict[str, Any]]:
    """Unstructured user representations."""

    return [
        {
            "id": "97108ac1-ffcb-411d-8b1e-d9183399f63b",
            "email": "superuser@example.com",
            "name": "Super User",
            "password": "Test_Password1!",
            "is_superuser": True,
            "is_active": True,
            "is_verified": True,
        },
        {
            "id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2",
            "email": "user@example.com",
            "name": "Example User",
            "password": "Test_Password2!",
            "is_superuser": False,
            "is_active": True,
            "is_verified": True,
        },
        {
            "id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e999",
            "email": "test@test.com",
            "name": "Test User",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
            "is_verified": True,
        },
        {
            "id": "6ef29f3c-3560-4d15-ba6b-a2e5c721e4d3",
            "email": "another@example.com",
            "name": "The User",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
            "is_verified": True,
        },
        {
            "id": "7ef29f3c-3560-4d15-ba6b-a2e5c721e4e1",
            "email": "inactive@example.com",
            "name": "Inactive User",
            "password": "Old_Password2!",
            "is_superuser": False,
            "is_active": False,
            "is_verified": False,
        },
    ]


@pytest.fixture(name="raw_teams")
def fx_raw_teams() -> list[Team | dict[str, Any]]:
    """Unstructured team representations."""

    return [
        {
            "id": "97108ac1-ffcb-411d-8b1e-d9183399f63b",
            "slug": "test-team",
            "name": "Test Team",
            "description": "This is a description for a  team.",
            "owner_id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2",
        },
        {
            "id": "81108ac1-ffcb-411d-8b1e-d91833999999",
            "slug": "simple-team",
            "name": "Simple Team",
            "description": "This is a description",
            "owner_id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e999",
            "tags": ["new", "another", "extra"],
        },
        {
            "id": "81108ac1-ffcb-411d-8b1e-d91833999998",
            "slug": "extra-team",
            "name": "Extra Team",
            "description": "This is a description",
            "owner_id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e999",
            "tags": ["extra"],
        },
    ]


@pytest.fixture(name="seeded_client")
async def fx_seeded_client(app: Litestar) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with seeded users.

    This fixture seeds test users directly into the app's database before yielding
    the test client. It uses its own user data to avoid mutation issues from
    other fixtures that may modify shared raw_users data.
    """
    from litestar.testing import AsyncTestClient
    from sqlalchemy import text

    from app.config import alchemy
    from app.db import models as m
    from app.lib.crypt import get_password_hash

    # Define users with passwords inline to avoid fixture mutation issues
    # The autouse _seed_db fixture in integration/conftest.py mutates raw_users,
    # replacing 'password' with 'hashed_password', so we need our own clean data
    test_users = [
        {
            "id": "97108ac1-ffcb-411d-8b1e-d9183399f63b",
            "email": "superuser@example.com",
            "name": "Super User",
            "password": "Test_Password1!",
            "is_superuser": True,
            "is_active": True,
            "is_verified": True,
        },
        {
            "id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2",
            "email": "user@example.com",
            "name": "Example User",
            "password": "Test_Password2!",
            "is_superuser": False,
            "is_active": True,
            "is_verified": True,
        },
        {
            "id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e999",
            "email": "test@test.com",
            "name": "Test User",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
            "is_verified": True,
        },
        {
            "id": "6ef29f3c-3560-4d15-ba6b-a2e5c721e4d3",
            "email": "another@example.com",
            "name": "The User",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
            "is_verified": True,
        },
        {
            "id": "7ef29f3c-3560-4d15-ba6b-a2e5c721e4e1",
            "email": "inactive@example.com",
            "name": "Inactive User",
            "password": "Old_Password2!",
            "is_superuser": False,
            "is_active": False,
            "is_verified": False,
        },
    ]

    async with alchemy.get_session() as session:
        # Delete existing test users and reseed for consistent state
        await session.execute(text("DELETE FROM user_account"))
        await session.commit()

        for user_data in test_users:
            user = m.User(
                id=UUID(user_data["id"]),
                email=user_data["email"],
                name=user_data["name"],
                hashed_password=await get_password_hash(user_data["password"]),
                is_superuser=user_data.get("is_superuser", False),
                is_active=user_data.get("is_active", True),
                is_verified=user_data.get("is_verified", True),
            )
            session.add(user)
        await session.commit()

    async with AsyncTestClient(app=app) as client:
        yield client
