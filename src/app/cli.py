from __future__ import annotations

from typing import Any

import anyio
import click
from pydantic import EmailStr
from rich import get_console

from app.domain.accounts.dtos import UserCreate, UserUpdate
from app.domain.accounts.services import UserService
from app.lib import log

__all__ = [
    "create_user",
    "user_management_app",
]


console = get_console()
"""Pre-configured CLI Console."""

logger = log.get_logger()


@click.group(name="users", invoke_without_command=False, help="Manage application users.")
@click.pass_context
def user_management_app(_: dict[str, Any]) -> None:
    """Manage application users."""


@user_management_app.command(name="create-user", help="Create a user")
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

    async def _create_user(
        email: str,
        name: str,
        password: str,
        superuser: bool = False,
    ) -> None:
        obj_in = UserCreate(
            email=EmailStr(email),
            name=name,
            password=password,
            is_superuser=superuser,
        )

        async with UserService.new() as users_service:
            user = await users_service.create(data=obj_in.__dict__)
            await users_service.repository.session.commit()
            logger.info("User created: %s", user.email)

    email = email or click.prompt("Email")
    name = name or click.prompt("Full Name", show_default=False)
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    superuser = superuser or click.prompt("Create as superuser?", show_default=True, type=click.BOOL)

    anyio.run(_create_user, email, name, password, superuser)


@user_management_app.command(name="promote-to-superuser", help="Promotes a user to application superuser")
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
        email (str): _description_
    """

    async def _promote_to_superuser(email: str) -> None:
        async with UserService.new() as users_service:
            user = await users_service.get_one_or_none(email=email)
            if user:
                logger.info("Promoting user: %s", user.email)
                user_in = UserUpdate(
                    email=user.email,
                    is_superuser=True,
                )
                user = await users_service.update(
                    item_id=user.id,
                    data=user_in.__dict__,
                )
                await users_service.repository.session.commit()
                logger.info("Upgraded %s to superuser", email)
            else:
                logger.warning("User not found: %s", email)

    anyio.run(_promote_to_superuser, email)
