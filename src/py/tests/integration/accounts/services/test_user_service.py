"""Comprehensive tests for UserService."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from litestar.exceptions import ClientException, PermissionDeniedException
from sqlalchemy import select
from sqlalchemy.orm import undefer_group

from app.domain.accounts.services._user import MAX_FAILED_RESET_ATTEMPTS
from app.lib.crypt import get_password_hash, verify_password
from app.lib.validation import PasswordValidationError
from tests.factories import RoleFactory, UserFactory, UserRoleFactory

if TYPE_CHECKING:
    from httpx_oauth.oauth2 import OAuth2Token
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.domain.accounts.services import UserService

pytestmark = [pytest.mark.anyio, pytest.mark.integration, pytest.mark.auth, pytest.mark.services]


async def test_authenticate_success(session: AsyncSession, user_service: UserService) -> None:
    """Test successful user authentication."""
    # Create user with known password
    password = "TestPassword123!"
    hashed_password = await get_password_hash(password)
    user = UserFactory.build(hashed_password=hashed_password, is_active=True)
    session.add(user)
    await session.commit()

    # Authenticate user
    authenticated_user = await user_service.authenticate(user.email, password)

    assert authenticated_user is not None
    assert authenticated_user.email == user.email
    assert authenticated_user.id == user.id


async def test_authenticate_user_not_found(user_service: UserService) -> None:
    """Test authentication with non-existent user fails."""
    with pytest.raises(PermissionDeniedException) as exc_info:
        await user_service.authenticate("nonexistent@example.com", "password")

    assert "User not found or password invalid" in str(exc_info.value)


async def test_authenticate_wrong_password(session: AsyncSession, user_service: UserService) -> None:
    """Test authentication with wrong password fails."""
    password = "TestPassword123!"
    hashed_password = await get_password_hash(password)
    user = UserFactory.build(hashed_password=hashed_password, is_active=True)
    session.add(user)
    await session.commit()

    with pytest.raises(PermissionDeniedException) as exc_info:
        await user_service.authenticate(user.email, "WrongPassword")

    assert "User not found or password invalid" in str(exc_info.value)


async def test_authenticate_inactive_user(session: AsyncSession, user_service: UserService) -> None:
    """Test authentication with inactive user fails."""
    password = "TestPassword123!"
    hashed_password = await get_password_hash(password)
    user = UserFactory.build(
        hashed_password=hashed_password,
        is_active=False,  # Inactive user
    )
    session.add(user)
    await session.commit()

    with pytest.raises(PermissionDeniedException) as exc_info:
        await user_service.authenticate(user.email, password)

    assert "User account is inactive" in str(exc_info.value)


async def test_authenticate_user_without_password(session: AsyncSession, user_service: UserService) -> None:
    """Test authentication with user that has no password (OAuth only)."""
    user = UserFactory.build(
        hashed_password=None,  # No password set
        is_active=True,
    )
    session.add(user)
    await session.commit()

    with pytest.raises(PermissionDeniedException) as exc_info:
        await user_service.authenticate(user.email, "anypassword")

    assert "User not found or password invalid" in str(exc_info.value)


async def test_verify_email_success(session: AsyncSession, user_service: UserService) -> None:
    """Test successful email verification."""
    user = UserFactory.build(is_verified=False)
    session.add(user)
    await session.commit()

    # Verify email
    updated_user = await user_service.verify_email(user.id, user.email)

    assert updated_user.is_verified is True
    assert updated_user.verified_at is not None


async def test_verify_email_user_not_found(user_service: UserService) -> None:
    """Test email verification with non-existent user."""
    from uuid import uuid4

    with pytest.raises(ClientException) as exc_info:
        await user_service.verify_email(uuid4(), "nonexistent@example.com")

    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value)


async def test_verify_email_mismatch(session: AsyncSession, user_service: UserService) -> None:
    """Test email verification with mismatched email."""
    user = UserFactory.build(is_verified=False)
    session.add(user)
    await session.commit()

    with pytest.raises(ClientException) as exc_info:
        await user_service.verify_email(user.id, "different@example.com")

    assert exc_info.value.status_code == 400
    assert "Email address does not match" in str(exc_info.value)


async def test_is_email_verified(session: AsyncSession, user_service: UserService) -> None:
    """Test checking email verification status."""
    verified_user = UserFactory.build(is_verified=True)
    unverified_user = UserFactory.build(is_verified=False)
    session.add_all([verified_user, unverified_user])
    await session.commit()

    assert await user_service.is_email_verified(verified_user.id) is True
    assert await user_service.is_email_verified(unverified_user.id) is False


async def test_is_email_verified_user_not_found(user_service: UserService) -> None:
    """Test email verification check with non-existent user."""
    from uuid import uuid4

    result = await user_service.is_email_verified(uuid4())
    assert result is False


async def test_require_verified_email_success(user_service: UserService) -> None:
    """Test require verified email with verified user."""
    user = UserFactory.build(is_verified=True)

    # Should not raise exception
    await user_service.require_verified_email(user)


async def test_require_verified_email_failure(user_service: UserService) -> None:
    """Test require verified email with unverified user."""
    user = UserFactory.build(is_verified=False)

    with pytest.raises(PermissionDeniedException) as exc_info:
        await user_service.require_verified_email(user)

    assert "Email verification required" in str(exc_info.value)


async def test_update_password_success(session: AsyncSession, user_service: UserService) -> None:
    """Test successful password update."""
    current_password = "CurrentPassword123!"
    new_password = "NewPassword123!"
    hashed_password = await get_password_hash(current_password)

    user = UserFactory.build(hashed_password=hashed_password, is_active=True)
    session.add(user)
    await session.commit()
    await session.refresh(user)  # Refresh to avoid lazy loading MissingGreenlet

    # Update password
    await user_service.update_password(
        data={"current_password": current_password, "new_password": new_password}, db_obj=user
    )

    # Re-fetch user with deferred security columns loaded using select()
    from app.db import models as m

    stmt = select(m.User).where(m.User.id == user.id).options(undefer_group("security_sensitive"))
    result = await session.execute(stmt)
    updated_user = result.scalar_one_or_none()
    assert updated_user is not None

    # Verify new password works
    assert updated_user.hashed_password is not None
    assert await verify_password(new_password, updated_user.hashed_password) is True
    # Verify old password doesn't work
    assert await verify_password(current_password, updated_user.hashed_password) is False


async def test_update_password_wrong_current_password(session: AsyncSession, user_service: UserService) -> None:
    """Test password update with wrong current password."""
    current_password = "CurrentPassword123!"
    hashed_password = await get_password_hash(current_password)

    user = UserFactory.build(hashed_password=hashed_password, is_active=True)
    session.add(user)
    await session.commit()

    with pytest.raises(PermissionDeniedException):
        await user_service.update_password(
            data={"current_password": "WrongPassword", "new_password": "NewPassword123!"}, db_obj=user
        )


async def test_update_password_inactive_user(session: AsyncSession, user_service: UserService) -> None:
    """Test password update with inactive user."""
    current_password = "CurrentPassword123!"
    hashed_password = await get_password_hash(current_password)

    user = UserFactory.build(hashed_password=hashed_password, is_active=False)
    session.add(user)
    await session.commit()

    with pytest.raises(PermissionDeniedException) as exc_info:
        await user_service.update_password(
            data={"current_password": current_password, "new_password": "NewPassword123!"}, db_obj=user
        )

    assert "User account is not active" in str(exc_info.value)


async def test_update_password_user_without_password(session: AsyncSession, user_service: UserService) -> None:
    """Test password update for user without password."""
    user = UserFactory.build(hashed_password=None, is_active=True)
    session.add(user)
    await session.commit()

    with pytest.raises(PermissionDeniedException):
        await user_service.update_password(
            data={"current_password": "anypassword", "new_password": "NewPassword123!"}, db_obj=user
        )


async def test_reset_password_with_token_success(session: AsyncSession, user_service: UserService) -> None:
    """Test successful password reset with token."""
    new_password = "NewPassword123!"
    user = UserFactory.build(
        hashed_password=await get_password_hash("OldPassword123!"),
        is_active=True,
        failed_reset_attempts=3,
        reset_locked_until=datetime.now(UTC),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)  # Refresh to avoid lazy loading MissingGreenlet

    # Reset password
    await user_service.reset_password_with_token(user.id, new_password)

    # Re-fetch user with deferred security columns loaded using select()
    from app.db import models as m

    stmt = select(m.User).where(m.User.id == user.id).options(undefer_group("security_sensitive"))
    result = await session.execute(stmt)
    updated_user = result.scalar_one_or_none()
    assert updated_user is not None

    # Verify password was updated
    assert updated_user.hashed_password is not None
    assert await verify_password(new_password, updated_user.hashed_password) is True
    # Verify security fields were reset
    assert updated_user.password_reset_at is not None
    assert updated_user.failed_reset_attempts == 0
    assert updated_user.reset_locked_until is None


async def test_reset_password_with_token_user_not_found(user_service: UserService) -> None:
    """Test password reset with non-existent user."""
    from uuid import uuid4

    with pytest.raises(ClientException) as exc_info:
        await user_service.reset_password_with_token(uuid4(), "NewPassword123!")

    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value)


async def test_reset_password_with_token_inactive_user(session: AsyncSession, user_service: UserService) -> None:
    """Test password reset with inactive user."""
    user = UserFactory.build(is_active=False)
    session.add(user)
    await session.commit()

    with pytest.raises(ClientException) as exc_info:
        await user_service.reset_password_with_token(user.id, "NewPassword123!")

    assert exc_info.value.status_code == 403
    assert "User account is inactive" in str(exc_info.value)


@patch("app.domain.accounts.services._user.validate_password_strength")
async def test_reset_password_with_token_weak_password(
    mock_validate: AsyncMock, session: AsyncSession, user_service: UserService
) -> None:
    """Test password reset with weak password."""
    mock_validate.side_effect = PasswordValidationError("Password too weak")

    user = UserFactory.build(is_active=True)
    session.add(user)
    await session.commit()
    await session.refresh(user)  # Refresh to avoid lazy loading MissingGreenlet

    with pytest.raises(ClientException) as exc_info:
        await user_service.reset_password_with_token(user.id, "weak")

    assert exc_info.value.status_code == 400
    assert "Password too weak" in str(exc_info.value)


async def test_is_reset_rate_limited_false(session: AsyncSession, user_service: UserService) -> None:
    """Test rate limiting check when not limited."""
    user = UserFactory.build(failed_reset_attempts=2, reset_locked_until=None)
    session.add(user)
    await session.commit()

    result = await user_service.is_reset_rate_limited(user.id)
    assert result is False


async def test_is_reset_rate_limited_true(session: AsyncSession, user_service: UserService) -> None:
    """Test rate limiting check when limited."""
    future_time = datetime.now(UTC).replace(hour=23, minute=59, second=59)
    user = UserFactory.build(failed_reset_attempts=MAX_FAILED_RESET_ATTEMPTS, reset_locked_until=future_time)
    session.add(user)
    await session.commit()

    result = await user_service.is_reset_rate_limited(user.id)
    assert result is True


async def test_is_reset_rate_limited_expired_lock(session: AsyncSession, user_service: UserService) -> None:
    """Test rate limiting check when lock has expired."""
    past_time = datetime.now(UTC).replace(year=2020)  # Past time
    user = UserFactory.build(failed_reset_attempts=MAX_FAILED_RESET_ATTEMPTS, reset_locked_until=past_time)
    session.add(user)
    await session.commit()

    result = await user_service.is_reset_rate_limited(user.id)
    assert result is False


async def test_is_reset_rate_limited_user_not_found(user_service: UserService) -> None:
    """Test rate limiting check with non-existent user."""
    from uuid import uuid4

    result = await user_service.is_reset_rate_limited(uuid4())
    assert result is False


async def test_increment_failed_reset_attempt(session: AsyncSession, user_service: UserService) -> None:
    """Test incrementing failed reset attempts."""
    user = UserFactory.build(failed_reset_attempts=0)
    session.add(user)
    await session.commit()
    initial_attempts = user.failed_reset_attempts

    await user_service.increment_failed_reset_attempt(user.id)
    await session.refresh(user)

    assert user.failed_reset_attempts == initial_attempts + 1


async def test_increment_failed_reset_attempt_max_reached(session: AsyncSession, user_service: UserService) -> None:
    """Test incrementing failed reset attempts when max is reached."""
    user = UserFactory.build(failed_reset_attempts=MAX_FAILED_RESET_ATTEMPTS - 1)
    session.add(user)
    await session.commit()

    await user_service.increment_failed_reset_attempt(user.id)
    await session.refresh(user)

    assert user.failed_reset_attempts == MAX_FAILED_RESET_ATTEMPTS
    assert user.reset_locked_until is not None
    assert user.reset_locked_until > datetime.now(UTC)


async def test_increment_failed_reset_attempt_user_not_found(user_service: UserService) -> None:
    """Test incrementing failed reset attempts with non-existent user."""
    from uuid import uuid4

    # Should not raise exception
    await user_service.increment_failed_reset_attempt(uuid4())


async def test_has_role_id_true(user_service: UserService) -> None:
    """Test has_role_id when user has the role."""
    from uuid import uuid4

    role_id = uuid4()
    user = UserFactory.build()

    role = RoleFactory.build(id=role_id)
    user_role = UserRoleFactory.build(user_id=user.id, role_id=role.id)
    user_role.role = role
    user.roles = [user_role]

    result = await user_service.has_role_id(user, role_id)
    assert result is True


async def test_has_role_id_false(user_service: UserService) -> None:
    """Test has_role_id when user doesn't have the role."""
    from uuid import uuid4

    role_id = uuid4()
    different_role_id = uuid4()
    user = UserFactory.build()

    role = RoleFactory.build(id=different_role_id)
    user_role = UserRoleFactory.build(user_id=user.id, role_id=role.id)
    user_role.role = role
    user.roles = [user_role]

    result = await user_service.has_role_id(user, role_id)
    assert result is False


async def test_has_role_true(user_service: UserService) -> None:
    """Test has_role when user has the role."""
    user = UserFactory.build()

    role = RoleFactory.build(name="admin")
    user_role = UserRoleFactory.build(user_id=user.id, role_id=role.id)
    user_role.role = role
    user.roles = [user_role]

    result = await user_service.has_role(user, "admin")
    assert result is True


async def test_has_role_false(user_service: UserService) -> None:
    """Test has_role when user doesn't have the role."""
    user = UserFactory.build()

    role = RoleFactory.build(name="user")
    user_role = UserRoleFactory.build(user_id=user.id, role_id=role.id)
    user_role.role = role
    user.roles = [user_role]

    result = await user_service.has_role(user, "admin")
    assert result is False


async def test_is_superuser_true_flag(user_service: UserService) -> None:
    """Test is_superuser when user has superuser flag."""
    user = UserFactory.build(is_superuser=True)
    user.roles = []

    result = user_service.is_superuser(user)
    assert result is True


async def test_is_superuser_true_role(user_service: UserService) -> None:
    """Test is_superuser when user has superuser role."""
    from app.lib import constants

    user = UserFactory.build(is_superuser=False)

    role = RoleFactory.build(name=constants.SUPERUSER_ACCESS_ROLE)
    user_role = UserRoleFactory.build(user_id=user.id, role_id=role.id)
    user_role.role = role
    user.roles = [user_role]

    result = user_service.is_superuser(user)
    assert result is True


async def test_is_superuser_false(user_service: UserService) -> None:
    """Test is_superuser when user is not superuser."""
    user = UserFactory.build(is_superuser=False)
    user.roles = []

    result = user_service.is_superuser(user)
    assert result is False


async def test_create_user_from_oauth(session: AsyncSession, user_service: UserService) -> None:
    """Test creating user from OAuth data."""
    oauth_data = {"email": "oauth@example.com", "name": "OAuth User", "id": "oauth_user_id"}

    token_data = cast(
        "OAuth2Token",
        {
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "token_type": "bearer",
            "expires_at": None,
        },
    )

    user = await user_service.create_user_from_oauth(oauth_data=oauth_data, provider="google", token_data=token_data)

    assert user.email == "oauth@example.com"
    assert user.name == "OAuth User"
    assert user.is_verified is True
    assert user.verified_at is not None
    assert user.is_active is True


@patch("app.domain.accounts.services._user_oauth_account.UserOAuthAccountService")
async def test_authenticate_or_create_oauth_user_existing(
    mock_oauth_service_class: AsyncMock, session: AsyncSession, user_service: UserService
) -> None:
    """Test OAuth authentication with existing user."""
    # Create existing user
    existing_user = UserFactory.build(email="oauth@example.com")
    session.add(existing_user)
    await session.commit()

    oauth_data = {"email": "oauth@example.com", "name": "OAuth User"}

    token_data = cast(
        "OAuth2Token",
        {
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "token_type": "bearer",
            "expires_at": None,
        },
    )

    # Mock the OAuth service
    mock_oauth_service = AsyncMock()
    mock_oauth_service_class.return_value = mock_oauth_service

    user, is_new = await user_service.authenticate_or_create_oauth_user(
        provider="google", oauth_data=oauth_data, token_data=token_data
    )

    assert user.id == existing_user.id
    assert is_new is False
    mock_oauth_service.create_or_update_oauth_account.assert_called_once()


@patch("app.domain.accounts.services._user_oauth_account.UserOAuthAccountService")
async def test_authenticate_or_create_oauth_user_new(
    mock_oauth_service_class: AsyncMock, session: AsyncSession, user_service: UserService
) -> None:
    """Test OAuth authentication with new user."""
    oauth_data = {"email": "newuser@example.com", "name": "New OAuth User"}

    token_data = cast(
        "OAuth2Token",
        {
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "token_type": "bearer",
            "expires_at": None,
        },
    )

    # Mock the OAuth service
    mock_oauth_service = AsyncMock()
    mock_oauth_service_class.return_value = mock_oauth_service

    user, is_new = await user_service.authenticate_or_create_oauth_user(
        provider="google", oauth_data=oauth_data, token_data=token_data
    )

    assert user.email == "newuser@example.com"
    assert user.name == "New OAuth User"
    assert is_new is True
    mock_oauth_service.create_or_update_oauth_account.assert_called_once()


async def test_create_user_with_password_hashing(session: AsyncSession, user_service: UserService) -> None:
    """Test user creation with password hashing."""
    from app.db import models as m

    unique_email = f"newuser_{uuid4().hex[:8]}@example.com"
    user_data = {"email": unique_email, "name": "New User", "password": "TestPassword123!"}

    created_user = await user_service.create(data=user_data)

    # Re-fetch with deferred security columns loaded using select() for proper options support
    stmt = select(m.User).where(m.User.id == created_user.id).options(undefer_group("security_sensitive"))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is not None

    assert user.email == unique_email
    assert user.name == "New User"
    assert user.hashed_password is not None
    assert user.hashed_password != "TestPassword123!"  # Should be hashed
    assert await verify_password("TestPassword123!", user.hashed_password) is True


async def test_get_user_by_email(session: AsyncSession, user_service: UserService) -> None:
    """Test getting user by email."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    found_user = await user_service.get_one_or_none(email=user.email)

    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.email == user.email


async def test_update_user(session: AsyncSession, user_service: UserService) -> None:
    """Test updating user information."""
    user = UserFactory.build(name="Original Name")
    session.add(user)
    await session.commit()

    updated_user = await user_service.update(item_id=user.id, data={"name": "Updated Name"})

    assert updated_user.name == "Updated Name"
    assert updated_user.id == user.id
