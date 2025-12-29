from __future__ import annotations

from typing import Any

import click


@click.group(name="users", invoke_without_command=False, help="Manage application users and roles.")
@click.pass_context
def user_management_group(_: dict[str, Any]) -> None:
    """Manage application users."""


async def load_database_fixtures() -> None:
    """Import/Synchronize Database Fixtures."""

    from pathlib import Path

    from advanced_alchemy.utils.fixtures import open_fixture_async
    from sqlalchemy import select
    from sqlalchemy.orm import load_only
    from structlog import get_logger

    from app.config import alchemy
    from app.db.models import Role
    from app.domain.accounts.services import RoleService
    from app.lib.settings import get_settings

    settings = get_settings()
    logger = get_logger()
    fixtures_path = Path(settings.db.FIXTURE_PATH)
    async with RoleService.new(
        statement=select(Role).options(load_only(Role.id, Role.slug, Role.name, Role.description)),
        config=alchemy,
    ) as service:
        fixture_data = await open_fixture_async(fixtures_path, "role")
        await service.upsert_many(match_fields=["name"], data=fixture_data, auto_commit=True)
        await logger.ainfo("loaded roles")


@user_management_group.command(name="create-user", help="Create a user")
@click.option(
    "--email",
    help="Email of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--name",
    help="Full name of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--password",
    help="Password",
    type=click.STRING,
    required=False,
    show_default=False,
)
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
    """Create a user."""
    from typing import cast

    import anyio
    import click
    from rich import get_console

    from app.config import alchemy
    from app.domain.accounts.deps import provide_users_service
    from app.domain.accounts.schemas import UserCreate

    console = get_console()

    async def _create_user(
        email: str,
        password: str,
        name: str | None = None,
        superuser: bool = False,
    ) -> None:
        obj_in = UserCreate(
            email=email,
            name=name,
            password=password,
            is_superuser=superuser,
        )
        async with alchemy.get_session() as db_session:
            users_service = await anext(provide_users_service(db_session))
            user = await users_service.create(data=obj_in.to_dict(), auto_commit=True)
            console.print(f"User created: {user.email}")

    console.rule("Create a new application user.")
    email = email or click.prompt("Email")
    name = name or click.prompt("Full Name", show_default=False)
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    superuser = superuser or click.prompt("Create as superuser?", show_default=True, type=click.BOOL)

    anyio.run(_create_user, cast("str", email), cast("str", password), name, cast("bool", superuser))


@user_management_group.command(name="promote-to-superuser", help="Promotes a user to application superuser")
@click.option(
    "--email",
    help="Email of the user",
    type=click.STRING,
    required=False,
    show_default=False,
)
def promote_to_superuser(email: str) -> None:
    """Promote to Superuser.

    Args:
        email (str): The email address of the user to promote.
    """
    import anyio
    from rich import get_console

    from app.config import alchemy
    from app.domain.accounts.schemas import UserUpdate
    from app.domain.accounts.services import UserService

    console = get_console()

    async def _promote_to_superuser(email: str) -> None:
        async with UserService.new(config=alchemy) as users_service:
            user = await users_service.get_one_or_none(email=email)
            if user:
                console.print(f"Promoting user: %{user.email}")
                user_in = UserUpdate(
                    email=user.email,
                    is_superuser=True,
                )
                user = await users_service.update(
                    item_id=user.id,
                    data=user_in.to_dict(),
                    auto_commit=True,
                )
                console.print(f"Upgraded {email} to superuser")
            else:
                console.print(f"User not found: {email}")

    console.rule("Promote user to superuser.")
    anyio.run(_promote_to_superuser, email)


@user_management_group.command(name="create-roles", help="Create pre-configured application roles and assign to users.")
def create_default_roles() -> None:
    """Create the default Roles for the system

    Args:
        email (str): The email address of the user to promote.
    """
    import anyio
    from advanced_alchemy.utils.text import slugify
    from rich import get_console

    from app.config import alchemy
    from app.db.models import UserRole
    from app.domain.accounts.deps import provide_users_service
    from app.domain.accounts.services import RoleService
    from app.lib.deps import create_service_provider

    provide_roles_service = create_service_provider(RoleService)
    console = get_console()

    async def _create_default_roles() -> None:
        await load_database_fixtures()
        async with alchemy.get_session() as db_session:
            users_service = await anext(provide_users_service(db_session))
            roles_service = await anext(provide_roles_service(db_session))
            default_role = await roles_service.get_one_or_none(slug=slugify(users_service.default_role))
            if default_role:
                all_active_users = await users_service.list(is_active=True)
                for user in all_active_users:
                    if any(r.role_id == default_role.id for r in user.roles):
                        console.print("User %s already has default role", user.email)
                    else:
                        user.roles.append(UserRole(role_id=default_role.id))
                        console.print("Assigned %s default role", user.email)
                        await users_service.update(item_id=user.id, data=user, auto_commit=False)
            await db_session.commit()

    console.rule("Creating default roles.")
    anyio.run(_create_default_roles)
