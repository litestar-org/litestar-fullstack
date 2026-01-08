from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
async def fx_seeded_client(app: Litestar, seeded_db: None) -> AsyncGenerator[AsyncClient, None]:
    """Create test client after seeding the database fixtures."""
    from litestar.testing import AsyncTestClient

    async with AsyncTestClient(app=app) as client:
        yield client
