"""Click CLI commands for user, role, and fixture administration."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import anyio
import click
import structlog
from advanced_alchemy.utils.fixtures import open_fixture_async
from advanced_alchemy.utils.text import slugify
from rich import get_console

from app.config import alchemy
from app.domain.accounts.schemas import UserCreate, UserUpdate
from app.domain.accounts.services import AccountServices
from app.lib.settings import get_settings

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar import SQLAlchemyAsyncConfig

logger = structlog.get_logger(__name__)


@click.group(name="users", invoke_without_command=False, help="Manage application users and roles.")
@click.pass_context
def user_management_group(_: dict[str, Any]) -> None:
    """Manage application users and roles."""


async def load_database_fixtures(alchemy_config: SQLAlchemyAsyncConfig | None = None) -> None:
    """Import and synchronize default role fixtures idempotently."""
    settings = get_settings()
    active_alchemy = alchemy_config or alchemy
    fixtures_path = Path(settings.db.FIXTURE_PATH)
    async with AccountServices.new(config=active_alchemy) as accounts:
        fixture_data = await open_fixture_async(fixtures_path, "role")
        await accounts.roles.upsert_many(match_fields=["name"], data=fixture_data, auto_commit=True)
        await logger.ainfo("Loaded role fixtures")


async def _create_user_async(
    email: str,
    password: str,
    name: str | None = None,
    superuser: bool = False,
    alchemy_config: SQLAlchemyAsyncConfig | None = None,
) -> str:
    active_alchemy = alchemy_config or alchemy
    obj_in = UserCreate(
        email=email,
        name=name,
        password=password,
        is_superuser=superuser,
    )
    async with AccountServices.new(config=active_alchemy) as accounts:
        user = await accounts.users.create(data=obj_in.to_dict(), auto_commit=True)
        return user.email


async def _promote_to_superuser_async(
    email: str,
    alchemy_config: SQLAlchemyAsyncConfig | None = None,
) -> bool:
    active_alchemy = alchemy_config or alchemy
    async with AccountServices.new(config=active_alchemy) as accounts:
        user = await accounts.users.get_one_or_none(email=email)
        if user is None:
            return False
        user_in = UserUpdate(email=user.email, is_superuser=True)
        await accounts.users.update(item_id=user.id, data=user_in.to_dict(), auto_commit=True)
        return True


async def _create_default_roles_async(alchemy_config: SQLAlchemyAsyncConfig | None = None) -> int:
    active_alchemy = alchemy_config or alchemy
    await load_database_fixtures(active_alchemy)
    assigned = 0
    async with AccountServices.new(config=active_alchemy) as accounts:
        default_role = await accounts.roles.get_one_or_none(slug=slugify(accounts.users.default_role))
        if default_role is None:
            default_role = await accounts.roles.create(
                data={
                    "name": accounts.users.default_role,
                    "slug": slugify(accounts.users.default_role),
                    "description": "Default application access role.",
                },
                auto_commit=True,
            )
        active_users = await accounts.users.get_many(is_active=True)
        now = datetime.now(UTC)
        for user in active_users:
            if any(role.role_id == default_role.id for role in user.roles):
                continue
            await accounts.user_roles.create(data={"user_id": user.id, "role_id": default_role.id, "assigned_at": now})
            assigned += 1
        await accounts.session.commit()
    return assigned


@user_management_group.command(name="create-user", help="Create a user")
@click.option("--email", help="Email of the new user", type=click.STRING, required=False, show_default=False)
@click.option("--name", help="Full name of the new user", type=click.STRING, required=False, show_default=False)
@click.option("--password", help="Password", type=click.STRING, required=False, show_default=False)
@click.option(
    "--superuser",
    help="Is a superuser",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=False,
    is_flag=True,
)
def create_user(
    email: str | None,
    name: str | None,
    password: str | None,
    superuser: bool | None,
) -> None:
    """Create a new application user."""
    console = get_console()
    console.rule("Create a new application user.")
    resolved_email = email or click.prompt("Email")
    resolved_name = name or click.prompt("Full Name", show_default=False)
    resolved_password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    resolved_superuser = (
        bool(superuser) if superuser is not None else click.confirm("Create as superuser?", default=False)
    )
    created_email = anyio.run(
        _create_user_async,
        cast("str", resolved_email),
        cast("str", resolved_password),
        resolved_name,
        resolved_superuser,
        alchemy,
    )
    console.print(f"User created: {created_email}")


@user_management_group.command(name="promote-to-superuser", help="Promotes a user to application superuser")
@click.option("--email", help="Email of the user", type=click.STRING, required=True, show_default=False)
def promote_to_superuser(email: str) -> None:
    """Promote an existing user account to superuser.

    Raises:
        click.ClickException: If no user matches ``email``.
    """
    console = get_console()
    console.rule("Promote user to superuser.")
    promoted = anyio.run(_promote_to_superuser_async, email, alchemy)
    if not promoted:
        msg = f"User not found: {email}"
        console.print(msg)
        raise click.ClickException(msg)
    console.print(f"Promoting user: {email}")
    console.print(f"Upgraded {email} to superuser")


@user_management_group.command(name="create-roles", help="Create pre-configured application roles and assign to users.")
def create_default_roles() -> None:
    """Load default roles from fixtures and assign the default role to active users lacking it."""
    console = get_console()
    console.rule("Creating default roles.")
    assigned = anyio.run(_create_default_roles_async, alchemy)
    console.print(f"Assigned default role to {assigned} user(s).")
