from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from app.config import base

if TYPE_CHECKING:
    from collections import abc
    from collections.abc import Iterator

    from litestar import Litestar
    from pytest import FixtureRequest, MonkeyPatch

    from app.db.models import Team, User

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: MonkeyPatch) -> None:
    """Path the settings."""

    settings = base.Settings.from_env(".env.testing")

    def get_settings(dotenv_filename: str = ".env.testing") -> base.Settings:
        return settings

    monkeypatch.setattr(base, "get_settings", get_settings)


@pytest.fixture(scope="session")
def event_loop() -> "abc.Iterator[asyncio.AbstractEventLoop]":
    """Scoped Event loop.

    Need the event loop scoped to the session so that we can use it to check
    containers are ready in session scoped containers fixture.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Adds Pytest ini config variables for the plugin."""
    parser.addini(
        "unit_test_pattern",
        (
            "Regex used to identify if a test is running as part of a unit or integration test "
            "suite. The pattern is matched against the path of each test function and affects the "
            "behavior of fixtures that are shared between unit and integration tests."
        ),
        type="string",
        default=r"^.*/tests/unit/.*$",
    )


@pytest.fixture(name="app")
def fx_app(pytestconfig: pytest.Config, monkeypatch: MonkeyPatch) -> Litestar:
    """App fixture.

    Returns:
        An application instance, configured via plugin.
    """
    from app.asgi import create_app

    return create_app()


@pytest.fixture(name="is_unit_test")
def fx_is_unit_test(request: FixtureRequest) -> bool:
    """Uses the ini option `unit_test_pattern` to determine if the test is part
    of unit or integration tests.
    """
    unittest_pattern: str = request.config.getini("unit_test_pattern")  # pyright:ignore
    return bool(re.search(unittest_pattern, str(request.path)))


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
        },
        {
            "id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2",
            "email": "user@example.com",
            "name": "Example User",
            "password": "Test_Password2!",
            "is_superuser": False,
            "is_active": True,
        },
        {
            "id": "5ef29f3c-3560-4d15-ba6b-a2e5c721e999",
            "email": "test@test.com",
            "name": "Test User",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
        },
        {
            "id": "6ef29f3c-3560-4d15-ba6b-a2e5c721e4d3",
            "email": "another@example.com",
            "name": "The User",
            "password": "Test_Password3!",
            "is_superuser": False,
            "is_active": True,
        },
        {
            "id": "7ef29f3c-3560-4d15-ba6b-a2e5c721e4e1",
            "email": "inactive@example.com",
            "name": "Inactive User",
            "password": "Old_Password2!",
            "is_superuser": False,
            "is_active": False,
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


@pytest.fixture()
def _patch_worker(
    is_unit_test: bool,
    monkeypatch: MonkeyPatch,
    event_loop: Iterator[asyncio.AbstractEventLoop],
) -> None:
    """We don't want the worker to start for unit tests."""
    if is_unit_test:
        from litestar_saq import base

        monkeypatch.setattr(base.Worker, "on_app_startup", MagicMock())
        monkeypatch.setattr(base.Worker, "stop", MagicMock())
