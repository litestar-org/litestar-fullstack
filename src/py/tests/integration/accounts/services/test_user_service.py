"""PostgreSQL integration tests for UserService."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar.exceptions import ClientException, PermissionDeniedException
from litestar_security.accounts import Argon2PasswordHasher
from sqlalchemy import select
from sqlalchemy.orm import undefer_group

from app.db import models as m
from app.lib import constants
from tests.factories import RoleFactory, UserFactory, UserRoleFactory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.domain.accounts.services import UserService

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.services]

_HASHER = Argon2PasswordHasher()


async def test_authenticate_success(session: AsyncSession, user_service: UserService) -> None:
    """Valid email and Argon2 password authenticate an active user."""
    password = "TestPassword123!"
    user = UserFactory.build(hashed_password=await _HASHER.hash(password), is_active=True)
    session.add(user)
    await session.commit()

    authenticated_user = await user_service.authenticate(user.email, password)
    assert authenticated_user.id == user.id
    assert authenticated_user.email == user.email


async def test_authenticate_rejects_wrong_password_inactive_and_passwordless(
    session: AsyncSession,
    user_service: UserService,
) -> None:
    """Authentication fails for wrong passwords, inactive users, passwordless accounts, and missing emails."""
    password = "TestPassword123!"
    hashed = await _HASHER.hash(password)
    active = UserFactory.build(hashed_password=hashed, is_active=True)
    inactive = UserFactory.build(hashed_password=hashed, is_active=False)
    passwordless = UserFactory.build(hashed_password=None, is_active=True)
    session.add_all([active, inactive, passwordless])
    await session.commit()

    with pytest.raises(PermissionDeniedException):
        await user_service.authenticate("missing@example.com", password)
    with pytest.raises(PermissionDeniedException):
        await user_service.authenticate(active.email, "WrongPassword!9")
    with pytest.raises(PermissionDeniedException, match="inactive"):
        await user_service.authenticate(inactive.email, password)
    with pytest.raises(PermissionDeniedException):
        await user_service.authenticate(passwordless.email, password)


async def test_verify_email_and_validation(session: AsyncSession, user_service: UserService) -> None:
    """Verifying email updates flags and rejects mismatched addresses or missing users."""
    user = UserFactory.build(is_verified=False, verified_at=None)
    session.add(user)
    await session.commit()

    with pytest.raises(ClientException) as not_found:
        await user_service.verify_email(uuid4(), "ghost@example.com")
    assert not_found.value.status_code == 404

    with pytest.raises(ClientException) as mismatch:
        await user_service.verify_email(user.id, "other@example.com")
    assert mismatch.value.status_code == 400

    updated = await user_service.verify_email(user.id, user.email)
    assert updated.is_verified is True
    assert updated.verified_at is not None


async def test_create_and_update_password_rotates_hash_and_epoch(
    session: AsyncSession,
    user_service: UserService,
) -> None:
    """Creating a user hashes passwords and updating password rotates the Argon2 hash and security epoch."""
    unique_email = f"newuser_{uuid4().hex[:8]}@example.com"
    created = await user_service.create(
        data={"email": unique_email, "name": "New User", "password": "CurrentPassword123!"},
        auto_commit=True,
    )
    created_id = created.id
    loaded = await session.scalar(
        select(m.User).where(m.User.id == created_id).options(undefer_group("security_sensitive"))
    )
    assert loaded is not None
    assert loaded.hashed_password is not None
    assert (await _HASHER.verify(loaded.hashed_password, "CurrentPassword123!")).verified is True
    initial_epoch = loaded.security_epoch

    await user_service.update_password(
        data={"current_password": "CurrentPassword123!", "new_password": "UpdatedPassword456!"},
        db_obj=loaded,
    )
    session.expire_all()
    refreshed = await session.scalar(
        select(m.User).where(m.User.id == created_id).options(undefer_group("security_sensitive"))
    )
    assert refreshed is not None
    assert refreshed.hashed_password is not None
    assert refreshed.security_epoch == initial_epoch + 1
    assert (await _HASHER.verify(refreshed.hashed_password, "UpdatedPassword456!")).verified is True
    assert (await _HASHER.verify(refreshed.hashed_password, "CurrentPassword123!")).verified is False


async def test_role_and_superuser_helpers(user_service: UserService) -> None:
    """Role and superuser helper checks inspect assigned roles and superuser flag."""
    role = RoleFactory.build(name=constants.SUPERUSER_ACCESS_ROLE)
    user = UserFactory.build(is_superuser=False)
    user_role = UserRoleFactory.build(user_id=user.id, role_id=role.id)
    user_role.role = role
    user.roles = [user_role]

    assert await user_service.has_role_id(user, role.id) is True
    assert await user_service.has_role(user, constants.SUPERUSER_ACCESS_ROLE) is True
    assert user_service.is_superuser(user) is True
