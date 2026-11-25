"""Unit tests for CLI user management and fixture seeding commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from advanced_alchemy.base import orm_registry
from click.testing import CliRunner

from app.cli import commands as cli_commands
from app.domain.accounts.services import AccountServices
from app.lib.settings import DatabaseSettings

if TYPE_CHECKING:
    from pathlib import Path

    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

pytestmark = pytest.mark.anyio


async def _init_cli_db(tmp_path: Path, name: str) -> SQLAlchemyAsyncConfig:
    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / name}").get_config()
    async with db_cfg.get_engine().begin() as conn:
        await conn.run_sync(orm_registry.metadata.create_all)
    return db_cfg


async def test_cli_fixture_idempotency_and_service_group_helpers(tmp_path: Path) -> None:
    db_cfg = await _init_cli_db(tmp_path, "cli_helpers.sqlite3")
    await cli_commands.load_database_fixtures(db_cfg)
    await cli_commands.load_database_fixtures(db_cfg)

    async with AccountServices.new(config=db_cfg) as accounts:
        roles, total = await accounts.roles.get_many_and_count()
        assert total >= 2
        assert {role.name for role in roles} >= {"Superuser", "Application Access"}

    created = await cli_commands._create_user_async(
        email="cli-user@example.com",
        password="StrongPassword!123",
        name="CLI User",
        superuser=False,
        alchemy_config=db_cfg,
    )
    assert created == "cli-user@example.com"

    assert await cli_commands._promote_to_superuser_async("cli-user@example.com", db_cfg) is True
    assert await cli_commands._promote_to_superuser_async("missing@example.com", db_cfg) is False

    assigned_first = await cli_commands._create_default_roles_async(db_cfg)
    assigned_second = await cli_commands._create_default_roles_async(db_cfg)
    assert assigned_first == 1
    assert assigned_second == 0

    async with AccountServices.new(config=db_cfg) as accounts:
        user = await accounts.users.get_one(email="cli-user@example.com")
        assert user.is_superuser is True
        assert len(user.roles) == 1


def test_cli_click_commands_via_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import anyio

    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / 'cli_runner.sqlite3'}").get_config()

    async def _setup() -> None:
        async with db_cfg.get_engine().begin() as conn:
            await conn.run_sync(orm_registry.metadata.create_all)

    anyio.run(_setup)
    monkeypatch.setattr(cli_commands, "alchemy", db_cfg)

    runner = CliRunner(env={"NO_COLOR": "1", "FORCE_COLOR": "0"})
    res_create = runner.invoke(
        cli_commands.user_management_group,
        ["create-user", "--email", "runner@example.com", "--name", "Runner", "--password", "StrongPassword!123"],
    )
    assert res_create.exit_code == 0, res_create.output
    assert "User created: runner@example.com" in res_create.output

    res_promote = runner.invoke(
        cli_commands.user_management_group,
        ["promote-to-superuser", "--email", "runner@example.com"],
    )
    assert res_promote.exit_code == 0, res_promote.output
    assert "Promoting user: runner@example.com" in res_promote.output
    assert "%" not in res_promote.output

    res_missing = runner.invoke(
        cli_commands.user_management_group,
        ["promote-to-superuser", "--email", "nobody@example.com"],
    )
    assert res_missing.exit_code != 0

    res_roles = runner.invoke(cli_commands.user_management_group, ["create-roles"])
    assert res_roles.exit_code == 0, res_roles.output
    assert "Assigned default role to 1 user(s)." in res_roles.output
