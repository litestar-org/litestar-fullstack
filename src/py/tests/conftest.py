from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.lib import settings as settings_lib

if TYPE_CHECKING:
    from pytest import MonkeyPatch


pytestmark = pytest.mark.anyio
pytest_plugins = [
    "tests.data_fixtures",
    "pytest_databases.docker",
    "pytest_databases.docker.postgres",
]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: MonkeyPatch) -> None:
    """Path the settings."""

    settings = settings_lib.Settings.from_env("src/py/tests/.env.testing")

    def get_settings(dotenv_filename: str = ".env.testing") -> settings_lib.Settings:
        return settings

    monkeypatch.setattr(settings_lib, "get_settings", get_settings)
