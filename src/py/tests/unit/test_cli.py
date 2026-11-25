"""Unit tests for CLI user management and fixture seeding commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click
import pytest
from advanced_alchemy.base import orm_registry
from click.testing import CliRunner

from app.cli import commands as cli_commands
from app.domain.accounts.services import AccountServices
from app.lib.constants import DEFAULT_ACCESS_ROLE, DEFAULT_ACCESS_ROLE_DESCRIPTION
from app.lib.settings import DatabaseSettings, get_settings

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

    async with AccountServices.new(config=db_cfg) as accounts:
        user = await accounts.users.get_one(email="cli-user@example.com")
        assert user.is_superuser is True
        assert user.is_verified is True
        assert [assigned.role_name for assigned in user.roles] == [DEFAULT_ACCESS_ROLE]
        roles, _ = await accounts.roles.get_many_and_count()
        assert {role.name for role in roles} == {DEFAULT_ACCESS_ROLE, "Superuser"}

    assert await cli_commands._create_default_roles_async(db_cfg) == 0


async def test_create_roles_adds_a_missing_default_access_role_the_way_sign_up_does(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_cfg = await _init_cli_db(tmp_path, "cli_default_role.sqlite3")
    (tmp_path / "role.json").write_text('[{"slug": "superuser", "name": "Superuser"}]')
    monkeypatch.setattr(get_settings().db, "FIXTURE_PATH", str(tmp_path))
    async with AccountServices.new(config=db_cfg) as accounts:
        await accounts.users.create({"email": "roleless@example.com", "password": "StrongPassword!123"})
        await accounts.session.commit()

    assert await cli_commands._create_default_roles_async(db_cfg) == 1

    async with AccountServices.new(config=db_cfg) as accounts:
        default_access_role = await accounts.roles.get_one(name=DEFAULT_ACCESS_ROLE)
        assert default_access_role.slug == "application-access"
        assert default_access_role.description == DEFAULT_ACCESS_ROLE_DESCRIPTION


def test_cli_click_commands_via_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import anyio

    db_cfg = DatabaseSettings(URL=f"sqlite+aiosqlite:///{tmp_path / 'cli_runner.sqlite3'}").get_config()

    async def _setup() -> None:
        async with db_cfg.get_engine().begin() as conn:
            await conn.run_sync(orm_registry.metadata.create_all)

    anyio.run(_setup)
    monkeypatch.setattr(cli_commands, "alchemy", db_cfg)

    runner = CliRunner()
    res_create = runner.invoke(
        cli_commands.user_management_group,
        ["create-user", "--email", "runner@example.com", "--name", "Runner", "--password", "StrongPassword!123"],
    )
    assert res_create.exit_code == 0, res_create.output
    assert "User created: runner@example.com" in click.unstyle(res_create.output)

    res_rejected = runner.invoke(
        cli_commands.user_management_group,
        ["create-user", "--email", "weak@example.com", "--name", "Weak", "--password", "Password12345"],
    )
    assert res_rejected.exit_code != 0
    assert "Password is too common" in click.unstyle(res_rejected.output)

    res_promote = runner.invoke(
        cli_commands.user_management_group,
        ["promote-to-superuser", "--email", "Runner@Example.com"],
    )
    assert res_promote.exit_code == 0, res_promote.output
    assert "Promoting user: Runner@Example.com" in click.unstyle(res_promote.output)
    assert "%" not in click.unstyle(res_promote.output)

    res_missing = runner.invoke(
        cli_commands.user_management_group,
        ["promote-to-superuser", "--email", "nobody@example.com"],
    )
    assert res_missing.exit_code != 0

    res_roles = runner.invoke(cli_commands.user_management_group, ["create-roles"])
    assert res_roles.exit_code == 0, res_roles.output
    assert "Assigned default role to 0 user(s)." in click.unstyle(res_roles.output)
