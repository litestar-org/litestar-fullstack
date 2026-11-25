"""PostgreSQL integration tests for UserService."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar_security.accounts import Argon2PasswordHasher
from sqlalchemy import select
from sqlalchemy.orm import undefer_group

from app.db import models as m

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.domain.accounts.services import UserService

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.services]

_HASHER = Argon2PasswordHasher()


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
        loaded,
        current_password="CurrentPassword123!",
        new_password="UpdatedPassword456!",
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
