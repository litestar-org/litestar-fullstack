"""Comprehensive tests for EmailVerificationTokenService."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from litestar.exceptions import ClientException

from app.db import models as m
from app.services._email_verification import EmailVerificationTokenService
from tests.factories import EmailVerificationTokenFactory, UserFactory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.services]


class TestEmailVerificationTokenCreation:
    """Test email verification token creation."""

    @pytest.mark.asyncio
    async def test_create_verification_token_success(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test successful verification token creation."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            token = await service.create_verification_token(user.id, user.email)

            assert token.user_id == user.id
            assert token.email == user.email
            assert token.token is not None
            assert len(token.token) >= 32  # URL-safe token should be substantial
            assert token.expires_at > datetime.now(UTC)
            assert token.used_at is None
            assert token.is_valid is True

    @pytest.mark.asyncio
    async def test_create_verification_token_invalidates_existing(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test that creating a new token invalidates existing ones."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Create first token
            first_token = await service.create_verification_token(user.id, user.email)
            assert first_token.is_valid is True

            # Create second token - should invalidate first
            second_token = await service.create_verification_token(user.id, user.email)

            # Refresh first token from database
            first_token_refreshed = await service.get_one(item_id=first_token.id)

            assert first_token_refreshed.is_used is True
            assert first_token_refreshed.used_at is not None
            assert second_token.is_valid is True
            assert second_token.id != first_token.id

    @pytest.mark.asyncio
    async def test_create_verification_token_different_emails(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test creating tokens for different emails doesn't interfere."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Create token for original email
            token1 = await service.create_verification_token(user.id, user.email)

            # Create token for different email
            token2 = await service.create_verification_token(user.id, "different@example.com")

            # Both tokens should be valid
            assert token1.is_valid is True
            assert token2.is_valid is True
            assert token1.email != token2.email

    @pytest.mark.asyncio
    async def test_create_verification_token_unique_tokens(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test that tokens are unique."""
        # Create two users
        user1 = UserFactory.build()
        user2 = UserFactory.build()
        session.add_all([user1, user2])
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            token1 = await service.create_verification_token(user1.id, user1.email)
            token2 = await service.create_verification_token(user2.id, user2.email)

            assert token1.token != token2.token
            assert token1.user_id != token2.user_id


class TestEmailVerificationTokenVerification:
    """Test email verification token verification."""

    @pytest.mark.asyncio
    async def test_verify_token_success(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test successful token verification."""
        # Create user and token
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            created_token = await service.create_verification_token(user.id, user.email)

            # Verify the token
            verified_token = await service.verify_token(created_token.token)

            assert verified_token.id == created_token.id
            assert verified_token.is_used is True
            assert verified_token.used_at is not None

    @pytest.mark.asyncio
    async def test_verify_invalid_token(
        self,
        sessionmaker,
    ) -> None:
        """Test verification of non-existent token."""
        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            with pytest.raises(ClientException) as exc_info:
                await service.verify_token("invalid_token")

            assert exc_info.value.status_code == 400
            assert "Invalid verification token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_expired_token(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test verification of expired token."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        # Create expired token manually
        expired_token = EmailVerificationTokenFactory.build(
            user_id=user.id,
            email=user.email,
            expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired 1 hour ago
        )
        session.add(expired_token)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            with pytest.raises(ClientException) as exc_info:
                await service.verify_token(expired_token.token)

            assert exc_info.value.status_code == 400
            assert "Verification token has expired" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_already_used_token(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test verification of already used token."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Create and verify token once
            created_token = await service.create_verification_token(user.id, user.email)
            await service.verify_token(created_token.token)

            # Try to verify again
            with pytest.raises(ClientException) as exc_info:
                await service.verify_token(created_token.token)

            assert exc_info.value.status_code == 400
            assert "Verification token has already been used" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_token_marks_as_used(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test that verification properly marks token as used."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            created_token = await service.create_verification_token(user.id, user.email)

            # Verify token is initially unused
            assert created_token.is_used is False
            assert created_token.used_at is None

            # Verify the token
            before_verify = datetime.now(UTC)
            verified_token = await service.verify_token(created_token.token)
            after_verify = datetime.now(UTC)

            # Check it's marked as used with correct timestamp
            assert verified_token.is_used is True
            assert verified_token.used_at is not None
            assert before_verify <= verified_token.used_at <= after_verify


class TestEmailVerificationTokenInvalidation:
    """Test token invalidation functionality."""

    @pytest.mark.asyncio
    async def test_invalidate_user_tokens_by_user_id(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test invalidating all tokens for a user."""
        # Create users
        user1 = UserFactory.build()
        user2 = UserFactory.build()
        session.add_all([user1, user2])
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Create tokens for both users
            user1_token1 = await service.create_verification_token(user1.id, user1.email)
            user1_token2 = await service.create_verification_token(user1.id, "alt@example.com")
            user2_token = await service.create_verification_token(user2.id, user2.email)

            # Invalidate user1's tokens
            await service.invalidate_user_tokens(user1.id)

            # Check user1's tokens are invalidated
            user1_token1_refreshed = await service.get_one(item_id=user1_token1.id)
            user1_token2_refreshed = await service.get_one(item_id=user1_token2.id)
            user2_token_refreshed = await service.get_one(item_id=user2_token.id)

            assert user1_token1_refreshed.is_used is True
            assert user1_token2_refreshed.is_used is True
            assert user2_token_refreshed.is_used is False  # Should not be affected

    @pytest.mark.asyncio
    async def test_invalidate_user_tokens_by_email(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test invalidating tokens for specific email."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Create tokens for different emails
            primary_token = await service.create_verification_token(user.id, user.email)
            alt_token = await service.create_verification_token(user.id, "alt@example.com")

            # Invalidate only primary email tokens
            await service.invalidate_user_tokens(user.id, user.email)

            # Check only primary email token is invalidated
            primary_token_refreshed = await service.get_one(item_id=primary_token.id)
            alt_token_refreshed = await service.get_one(item_id=alt_token.id)

            assert primary_token_refreshed.is_used is True
            assert alt_token_refreshed.is_used is False

    @pytest.mark.asyncio
    async def test_invalidate_user_tokens_no_tokens(
        self,
        sessionmaker,
    ) -> None:
        """Test invalidating tokens when user has no tokens."""
        from uuid import uuid4

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Should not raise error even if no tokens exist
            await service.invalidate_user_tokens(uuid4())

    @pytest.mark.asyncio
    async def test_invalidate_user_tokens_already_used(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test invalidating tokens when some are already used."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Create tokens
            token1 = await service.create_verification_token(user.id, user.email)
            token2 = await service.create_verification_token(user.id, "alt@example.com")

            # Use one token
            await service.verify_token(token1.token)

            # Invalidate all tokens
            await service.invalidate_user_tokens(user.id)

            # Both tokens should remain marked as used
            token1_refreshed = await service.get_one(item_id=token1.id)
            token2_refreshed = await service.get_one(item_id=token2.id)

            assert token1_refreshed.is_used is True
            assert token2_refreshed.is_used is True


class TestEmailVerificationTokenCleanup:
    """Test token cleanup functionality."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_success(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test cleaning up expired tokens."""
        # Create users
        user1 = UserFactory.build()
        user2 = UserFactory.build()
        session.add_all([user1, user2])
        await session.commit()

        # Create expired tokens
        expired_token1 = EmailVerificationTokenFactory.build(
            user_id=user1.id, email=user1.email, expires_at=datetime.now(UTC) - timedelta(hours=1)
        )
        expired_token2 = EmailVerificationTokenFactory.build(
            user_id=user2.id, email=user2.email, expires_at=datetime.now(UTC) - timedelta(hours=2)
        )

        # Create valid token
        valid_token = EmailVerificationTokenFactory.build(
            user_id=user1.id, email="alt@example.com", expires_at=datetime.now(UTC) + timedelta(hours=1)
        )

        session.add_all([expired_token1, expired_token2, valid_token])
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Clean up expired tokens
            cleanup_count = await service.cleanup_expired_tokens()

            assert cleanup_count == 2

            # Verify expired tokens are deleted
            expired_token1_check = await service.get_one_or_none(item_id=expired_token1.id)
            expired_token2_check = await service.get_one_or_none(item_id=expired_token2.id)
            valid_token_check = await service.get_one_or_none(item_id=valid_token.id)

            assert expired_token1_check is None
            assert expired_token2_check is None
            assert valid_token_check is not None

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_no_expired(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test cleanup when no tokens are expired."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        # Create only valid tokens
        valid_token1 = EmailVerificationTokenFactory.build(
            user_id=user.id, email=user.email, expires_at=datetime.now(UTC) + timedelta(hours=1)
        )
        valid_token2 = EmailVerificationTokenFactory.build(
            user_id=user.id, email="alt@example.com", expires_at=datetime.now(UTC) + timedelta(hours=2)
        )

        session.add_all([valid_token1, valid_token2])
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            cleanup_count = await service.cleanup_expired_tokens()

            assert cleanup_count == 0

            # Verify tokens still exist
            valid_token1_check = await service.get_one_or_none(item_id=valid_token1.id)
            valid_token2_check = await service.get_one_or_none(item_id=valid_token2.id)

            assert valid_token1_check is not None
            assert valid_token2_check is not None

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens_empty_database(
        self,
        sessionmaker,
    ) -> None:
        """Test cleanup with no tokens in database."""
        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            cleanup_count = await service.cleanup_expired_tokens()
            assert cleanup_count == 0


class TestEmailVerificationTokenModel:
    """Test EmailVerificationToken model properties."""

    def test_is_expired_property_true(self) -> None:
        """Test is_expired property when token is expired."""
        token = EmailVerificationTokenFactory.build(expires_at=datetime.now(UTC) - timedelta(hours=1))
        assert token.is_expired is True

    def test_is_expired_property_false(self) -> None:
        """Test is_expired property when token is not expired."""
        token = EmailVerificationTokenFactory.build(expires_at=datetime.now(UTC) + timedelta(hours=1))
        assert token.is_expired is False

    def test_is_used_property_true(self) -> None:
        """Test is_used property when token is used."""
        token = EmailVerificationTokenFactory.build(used_at=datetime.now(UTC))
        assert token.is_used is True

    def test_is_used_property_false(self) -> None:
        """Test is_used property when token is not used."""
        token = EmailVerificationTokenFactory.build(used_at=None)
        assert token.is_used is False

    def test_is_valid_property_true(self) -> None:
        """Test is_valid property when token is valid."""
        token = EmailVerificationTokenFactory.build(expires_at=datetime.now(UTC) + timedelta(hours=1), used_at=None)
        assert token.is_valid is True

    def test_is_valid_property_false_expired(self) -> None:
        """Test is_valid property when token is expired."""
        token = EmailVerificationTokenFactory.build(expires_at=datetime.now(UTC) - timedelta(hours=1), used_at=None)
        assert token.is_valid is False

    def test_is_valid_property_false_used(self) -> None:
        """Test is_valid property when token is used."""
        token = EmailVerificationTokenFactory.build(
            expires_at=datetime.now(UTC) + timedelta(hours=1), used_at=datetime.now(UTC)
        )
        assert token.is_valid is False

    def test_create_expires_at_default(self) -> None:
        """Test create_expires_at with default 24 hours."""
        before = datetime.now(UTC)
        expires_at = m.EmailVerificationToken.create_expires_at()
        after = datetime.now(UTC)

        expected_min = before + timedelta(hours=24)
        expected_max = after + timedelta(hours=24)

        assert expected_min <= expires_at <= expected_max

    def test_create_expires_at_custom_hours(self) -> None:
        """Test create_expires_at with custom hours."""
        before = datetime.now(UTC)
        expires_at = m.EmailVerificationToken.create_expires_at(hours=12)
        after = datetime.now(UTC)

        expected_min = before + timedelta(hours=12)
        expected_max = after + timedelta(hours=12)

        assert expected_min <= expires_at <= expected_max


class TestEmailVerificationTokenIntegration:
    """Integration tests for email verification workflow."""

    @pytest.mark.asyncio
    async def test_full_verification_workflow(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test complete email verification workflow."""
        # Create user
        user = UserFactory.build(is_verified=False)
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # 1. Create verification token
            token = await service.create_verification_token(user.id, user.email)
            assert token.is_valid is True

            # 2. Verify token
            verified_token = await service.verify_token(token.token)
            assert verified_token.is_used is True

            # 3. Try to verify again (should fail)
            with pytest.raises(ClientException):
                await service.verify_token(token.token)

    @pytest.mark.asyncio
    async def test_multiple_email_verification_workflow(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test verification workflow with multiple email addresses."""
        # Create user
        user = UserFactory.build()
        session.add(user)
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Create tokens for different emails
            primary_token = await service.create_verification_token(user.id, user.email)
            alt_token = await service.create_verification_token(user.id, "alt@example.com")

            # Verify primary email
            await service.verify_token(primary_token.token)

            # Alt email token should still be valid
            alt_token_refreshed = await service.get_one(item_id=alt_token.id)
            assert alt_token_refreshed.is_valid is True

            # Verify alt email
            await service.verify_token(alt_token.token)

    @pytest.mark.asyncio
    async def test_token_security_properties(
        self,
        session: AsyncSession,
        sessionmaker,
    ) -> None:
        """Test security properties of tokens."""
        # Create users
        user1 = UserFactory.build()
        user2 = UserFactory.build()
        session.add_all([user1, user2])
        await session.commit()

        async with EmailVerificationTokenService.new(sessionmaker()) as service:
            # Create many tokens
            tokens = []
            for _ in range(10):
                token = await service.create_verification_token(user1.id, user1.email)
                tokens.append(token.token)

            # Verify all tokens are unique
            assert len(set(tokens)) == len(tokens)

            # Verify tokens are sufficiently long
            for token_str in tokens:
                assert len(token_str) >= 32
                # Should be URL-safe (base64 characters only)
                import string

                allowed_chars = string.ascii_letters + string.digits + "-_"
                assert all(c in allowed_chars for c in token_str)
