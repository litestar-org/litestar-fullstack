"""Comprehensive tests for PasswordResetService."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from litestar.exceptions import ClientException

from app.db import models as m
from app.domain.accounts.services import PasswordResetService
from tests.factories import PasswordResetTokenFactory, UserFactory, get_raw_token

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.integration, pytest.mark.auth, pytest.mark.services, pytest.mark.security]


@pytest.mark.anyio
async def test_create_reset_token_success(
    session: AsyncSession,
) -> None:
    """Test successful password reset token creation."""
    # Create user
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        token, raw_token = await service.create_reset_token(user.id, ip_address="127.0.0.1", user_agent="Test Browser")

        assert token.user_id == user.id
        assert raw_token is not None
        assert len(raw_token) >= 32
        assert token.expires_at > datetime.now(UTC)
        assert token.used_at is None
        assert token.ip_address == "127.0.0.1"
        assert token.user_agent == "Test Browser"
        assert token.is_valid is True


@pytest.mark.anyio
async def test_create_reset_token_without_metadata(
    session: AsyncSession,
) -> None:
    """Test token creation without IP/user agent."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        token, raw_token = await service.create_reset_token(user.id)

        assert token.user_id == user.id
        assert raw_token is not None
        assert token.ip_address is None
        assert token.user_agent is None
        assert token.is_valid is True


@pytest.mark.anyio
async def test_create_reset_token_invalidates_existing(
    session: AsyncSession,
) -> None:
    """Test that creating a new token invalidates existing ones."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # Create first token
        first_token, _ = await service.create_reset_token(user.id)
        assert first_token.is_valid is True

        # Create second token - should invalidate first
        second_token, _ = await service.create_reset_token(user.id)

        # Refresh first token from database
        first_token_refreshed = await service.get_one(id=first_token.id)

        assert first_token_refreshed.is_used is True
        assert first_token_refreshed.used_at is not None
        assert second_token.is_valid is True
        assert second_token.id != first_token.id


@pytest.mark.anyio
async def test_create_reset_token_short_expiration(
    session: AsyncSession,
) -> None:
    """Test that reset tokens have short expiration (1 hour)."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        before_creation = datetime.now(UTC)
        token, _ = await service.create_reset_token(user.id)
        after_creation = datetime.now(UTC)

        # Token should expire in approximately 1 hour
        expected_min_expiry = before_creation + timedelta(hours=1)
        expected_max_expiry = after_creation + timedelta(hours=1)

        assert expected_min_expiry <= token.expires_at <= expected_max_expiry


@pytest.mark.anyio
async def test_create_reset_token_unique_tokens(
    session: AsyncSession,
) -> None:
    """Test that tokens are unique across different users."""
    user1 = UserFactory.build()
    user2 = UserFactory.build()
    session.add_all([user1, user2])
    await session.commit()

    async with PasswordResetService.new(session) as service:
        token1, raw_token1 = await service.create_reset_token(user1.id)
        token2, raw_token2 = await service.create_reset_token(user2.id)

        assert raw_token1 != raw_token2
        assert token1.user_id != token2.user_id


@pytest.mark.anyio
async def test_validate_reset_token_success(
    session: AsyncSession,
) -> None:
    """Test successful token validation."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        created_token, raw_token = await service.create_reset_token(user.id)

        # Validate the token
        validated_token = await service.validate_reset_token(raw_token)

        assert validated_token is not None
        assert validated_token.id == created_token.id
        assert validated_token.is_valid is True
        # Validation should not consume the token
        assert validated_token.is_used is False


@pytest.mark.anyio
async def test_validate_invalid_token(
    session: AsyncSession,
) -> None:
    """Test validation of non-existent token."""
    async with PasswordResetService.new(session) as service:
        with pytest.raises(ClientException) as exc_info:
            await service.validate_reset_token("invalid_token")

        assert exc_info.value.status_code == 400
        assert "Invalid reset token" in str(exc_info.value)


@pytest.mark.anyio
async def test_validate_expired_token(
    session: AsyncSession,
) -> None:
    """Test validation of expired token."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    # Create expired token manually
    expired_token = PasswordResetTokenFactory.build(
        user_id=user.id,
        expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired 1 hour ago
    )
    session.add(expired_token)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        with pytest.raises(ClientException) as exc_info:
            await service.validate_reset_token(get_raw_token(expired_token))

        assert exc_info.value.status_code == 400
        assert "Reset token has expired" in str(exc_info.value)


@pytest.mark.anyio
async def test_validate_used_token(
    session: AsyncSession,
) -> None:
    """Test validation of already used token."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    # Create used token manually
    used_token = PasswordResetTokenFactory.build(user_id=user.id, used_at=datetime.now(UTC))
    session.add(used_token)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        with pytest.raises(ClientException) as exc_info:
            await service.validate_reset_token(get_raw_token(used_token))

        assert exc_info.value.status_code == 400
        assert "Reset token has already been used" in str(exc_info.value)


@pytest.mark.anyio
async def test_use_reset_token_success(
    session: AsyncSession,
) -> None:
    """Test successful token usage."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        created_token, raw_token = await service.create_reset_token(user.id)

        # Use the token
        before_use = datetime.now(UTC)
        used_token = await service.use_reset_token(raw_token)
        after_use = datetime.now(UTC)

        assert used_token.id == created_token.id
        assert used_token.is_used is True
        assert used_token.used_at is not None
        assert before_use <= used_token.used_at <= after_use


@pytest.mark.anyio
async def test_use_invalid_token(
    session: AsyncSession,
) -> None:
    """Test using non-existent token."""
    async with PasswordResetService.new(session) as service:
        with pytest.raises(ClientException) as exc_info:
            await service.use_reset_token("invalid_token")

        assert exc_info.value.status_code == 400
        assert "Invalid reset token" in str(exc_info.value)


@pytest.mark.anyio
async def test_use_expired_token(
    session: AsyncSession,
) -> None:
    """Test using expired token."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    expired_token = PasswordResetTokenFactory.build(user_id=user.id, expires_at=datetime.now(UTC) - timedelta(hours=1))
    session.add(expired_token)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        with pytest.raises(ClientException) as exc_info:
            await service.use_reset_token(get_raw_token(expired_token))

        assert exc_info.value.status_code == 400
        assert "Reset token has expired" in str(exc_info.value)


@pytest.mark.anyio
async def test_use_already_used_token(
    session: AsyncSession,
) -> None:
    """Test using token twice."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        _created_token, raw_token = await service.create_reset_token(user.id)

        # Use token first time
        await service.use_reset_token(raw_token)

        # Try to use again
        with pytest.raises(ClientException) as exc_info:
            await service.use_reset_token(raw_token)

        assert exc_info.value.status_code == 400
        assert "Reset token has already been used" in str(exc_info.value)


@pytest.mark.anyio
async def test_invalidate_user_tokens(
    session: AsyncSession,
) -> None:
    """Test invalidating all tokens for a user."""
    user1 = UserFactory.build()
    user2 = UserFactory.build()
    session.add_all([user1, user2])
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # Create tokens for both users
        user1_token1, _ = await service.create_reset_token(user1.id)
        user1_token2 = PasswordResetTokenFactory.build(user_id=user1.id)
        user2_token, _ = await service.create_reset_token(user2.id)

        session.add(user1_token2)
        await session.commit()

        # Invalidate user1's tokens
        await service.invalidate_user_tokens(user1.id)

        # Check user1's tokens are invalidated
        user1_token1_refreshed = await service.get_one(id=user1_token1.id)
        user1_token2_refreshed = await service.get_one(id=user1_token2.id)
        user2_token_refreshed = await service.get_one(id=user2_token.id)

        assert user1_token1_refreshed.is_used is True
        assert user1_token2_refreshed.is_used is True
        assert user2_token_refreshed.is_used is False  # Should not be affected


@pytest.mark.anyio
async def test_invalidate_user_tokens_no_tokens(
    session: AsyncSession,
) -> None:
    """Test invalidating tokens when user has no tokens."""
    from uuid import uuid4

    async with PasswordResetService.new(session) as service:
        # Should not raise error even if no tokens exist
        await service.invalidate_user_tokens(uuid4())


@pytest.mark.anyio
async def test_invalidate_user_tokens_already_used(
    session: AsyncSession,
) -> None:
    """Test invalidating tokens when some are already used."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # Create tokens
        token1, raw_token1 = await service.create_reset_token(user.id)
        token2 = PasswordResetTokenFactory.build(user_id=user.id)
        session.add(token2)
        await session.commit()

        # Use one token
        await service.use_reset_token(raw_token1)

        # Invalidate all tokens
        await service.invalidate_user_tokens(user.id)

        # Both tokens should remain marked as used
        token1_refreshed = await service.get_one(id=token1.id)
        token2_refreshed = await service.get_one(id=token2.id)

        assert token1_refreshed.is_used is True
        assert token2_refreshed.is_used is True


@pytest.mark.anyio
async def test_cleanup_expired_tokens_success(
    session: AsyncSession,
) -> None:
    """Test cleaning up expired tokens."""
    user1 = UserFactory.build()
    user2 = UserFactory.build()
    session.add_all([user1, user2])
    await session.commit()

    # Create expired tokens
    expired_token1 = PasswordResetTokenFactory.build(
        user_id=user1.id, expires_at=datetime.now(UTC) - timedelta(hours=1)
    )
    expired_token2 = PasswordResetTokenFactory.build(
        user_id=user2.id, expires_at=datetime.now(UTC) - timedelta(hours=2)
    )

    # Create valid token
    valid_token = PasswordResetTokenFactory.build(user_id=user1.id, expires_at=datetime.now(UTC) + timedelta(hours=1))

    session.add_all([expired_token1, expired_token2, valid_token])
    await session.commit()

    async with PasswordResetService.new(session) as service:
        cleanup_count = await service.cleanup_expired_tokens()

        assert cleanup_count == 2

        # Verify expired tokens are deleted
        expired_token1_check = await service.get_one_or_none(id=expired_token1.id)
        expired_token2_check = await service.get_one_or_none(id=expired_token2.id)
        valid_token_check = await service.get_one_or_none(id=valid_token.id)

        assert expired_token1_check is None
        assert expired_token2_check is None
        assert valid_token_check is not None


@pytest.mark.anyio
async def test_cleanup_expired_tokens_no_expired(
    session: AsyncSession,
) -> None:
    """Test cleanup when no tokens are expired."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    # Create only valid tokens
    valid_token1 = PasswordResetTokenFactory.build(user_id=user.id, expires_at=datetime.now(UTC) + timedelta(hours=1))
    valid_token2 = PasswordResetTokenFactory.build(user_id=user.id, expires_at=datetime.now(UTC) + timedelta(hours=2))

    session.add_all([valid_token1, valid_token2])
    await session.commit()

    async with PasswordResetService.new(session) as service:
        cleanup_count = await service.cleanup_expired_tokens()

        assert cleanup_count == 0

        # Verify tokens still exist
        valid_token1_check = await service.get_one_or_none(id=valid_token1.id)
        valid_token2_check = await service.get_one_or_none(id=valid_token2.id)

        assert valid_token1_check is not None
        assert valid_token2_check is not None


@pytest.mark.anyio
async def test_cleanup_expired_tokens_empty_database(
    session: AsyncSession,
) -> None:
    """Test cleanup with no tokens in database."""
    async with PasswordResetService.new(session) as service:
        cleanup_count = await service.cleanup_expired_tokens()
        assert cleanup_count == 0


@pytest.mark.anyio
async def test_check_rate_limit_not_exceeded(
    session: AsyncSession,
) -> None:
    """Test rate limit check when limit not exceeded."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # Create 2 tokens (under the limit of 3)
        await service.create_reset_token(user.id)
        await service.create_reset_token(user.id)

        is_rate_limited = await service.check_rate_limit(user.id)
        assert is_rate_limited is False


@pytest.mark.anyio
async def test_check_rate_limit_exceeded(
    session: AsyncSession,
) -> None:
    """Test rate limit check when limit exceeded."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # Create 3 tokens (at the limit)
        await service.create_reset_token(user.id)
        await service.create_reset_token(user.id)
        await service.create_reset_token(user.id)

        is_rate_limited = await service.check_rate_limit(user.id)
        assert is_rate_limited is True


@pytest.mark.anyio
async def test_check_rate_limit_old_tokens_ignored(
    session: AsyncSession,
) -> None:
    """Test that old tokens don't count towards rate limit."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    # Create old tokens (outside the 1-hour window)
    old_token1 = PasswordResetTokenFactory.build(user_id=user.id, created_at=datetime.now(UTC) - timedelta(hours=2))
    old_token2 = PasswordResetTokenFactory.build(user_id=user.id, created_at=datetime.now(UTC) - timedelta(hours=3))
    session.add_all([old_token1, old_token2])
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # Create new token
        await service.create_reset_token(user.id)

        # Should not be rate limited since old tokens don't count
        is_rate_limited = await service.check_rate_limit(user.id)
        assert is_rate_limited is False


@pytest.mark.anyio
async def test_check_rate_limit_custom_hours(
    session: AsyncSession,
) -> None:
    """Test rate limit check with custom hour window."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    # Create token 30 minutes ago
    token = PasswordResetTokenFactory.build(user_id=user.id, created_at=datetime.now(UTC) - timedelta(minutes=30))
    session.add(token)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # With 1-hour window, should count the token
        is_rate_limited_1h = await service.check_rate_limit(user.id, hours=1)
        # With 15-minute window, should not count the token
        is_rate_limited_15m = await service.check_rate_limit(user.id, hours=0.25)

        assert is_rate_limited_1h is False  # 1 token is under limit
        assert is_rate_limited_15m is False  # Token is outside 15-minute window


@pytest.mark.anyio
async def test_check_rate_limit_no_tokens(
    session: AsyncSession,
) -> None:
    """Test rate limit check with no existing tokens."""
    from uuid import uuid4

    async with PasswordResetService.new(session) as service:
        is_rate_limited = await service.check_rate_limit(uuid4())
        assert is_rate_limited is False


@pytest.mark.anyio
async def test_full_password_reset_workflow(
    session: AsyncSession,
) -> None:
    """Test complete password reset workflow."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # 1. Create reset token
        token, raw_token = await service.create_reset_token(user.id, "127.0.0.1", "Test Browser")
        assert token.is_valid is True

        # 2. Validate token (like checking if reset link is valid)
        validated_token = await service.validate_reset_token(raw_token)
        assert validated_token.is_valid is True

        # 3. Use token (when user submits new password)
        used_token = await service.use_reset_token(raw_token)
        assert used_token.is_used is True

        # 4. Try to use again (should fail)
        with pytest.raises(ClientException):
            await service.use_reset_token(raw_token)


@pytest.mark.anyio
async def test_security_features_integration(
    session: AsyncSession,
) -> None:
    """Test security features working together."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # Test rate limiting
        await service.create_reset_token(user.id)
        await service.create_reset_token(user.id)
        await service.create_reset_token(user.id)

        # Should be rate limited now
        is_rate_limited = await service.check_rate_limit(user.id)
        assert is_rate_limited is True

        # Test token invalidation on new request
        valid_token, _ = await service.create_reset_token(user.id)

        # All previous tokens should be invalidated
        tokens = await service.repository.list(m.PasswordResetToken.user_id == user.id)
        used_tokens = [t for t in tokens if t.is_used and t.id != valid_token.id]
        assert len(used_tokens) >= 3  # Previous tokens should be invalidated


@pytest.mark.anyio
async def test_token_security_properties(
    session: AsyncSession,
) -> None:
    """Test security properties of reset tokens."""
    user1 = UserFactory.build()
    user2 = UserFactory.build()
    session.add_all([user1, user2])
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # Create many tokens
        tokens = []
        for _ in range(10):
            _, raw_token = await service.create_reset_token(user1.id)
            tokens.append(raw_token)

        # Verify all tokens are unique
        assert len(set(tokens)) == len(tokens)

        # Verify tokens are sufficiently long and secure
        for token_str in tokens:
            assert len(token_str) >= 32
            # Should be URL-safe (base64 characters only)
            import string

            allowed_chars = string.ascii_letters + string.digits + "-_"
            assert all(c in allowed_chars for c in token_str)


@pytest.mark.anyio
async def test_concurrent_reset_requests(
    session: AsyncSession,
) -> None:
    """Test handling concurrent reset requests."""
    user = UserFactory.build()
    session.add(user)
    await session.commit()

    async with PasswordResetService.new(session) as service:
        # Simulate concurrent requests by creating tokens in sequence
        token1, _ = await service.create_reset_token(user.id, "192.168.1.1", "Browser 1")
        token2, _ = await service.create_reset_token(user.id, "192.168.1.2", "Browser 2")

        # Only the latest token should be valid
        token1_refreshed = await service.get_one(id=token1.id)
        token2_refreshed = await service.get_one(id=token2.id)

        assert token1_refreshed.is_used is True
        assert token2_refreshed.is_valid is True

        # Different IP addresses should be preserved
        assert token1.ip_address == "192.168.1.1"
        assert token2.ip_address == "192.168.1.2"
