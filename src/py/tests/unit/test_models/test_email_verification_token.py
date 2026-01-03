"""Unit tests for EmailVerificationToken model."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.db import models as m


class TestEmailVerificationToken:
    """Test EmailVerificationToken model."""

    def test_create_expires_at_default(self) -> None:
        """Test create_expires_at with default 24 hours."""
        before = datetime.now(UTC)
        expires_at = m.EmailVerificationToken.create_expires_at()
        after = datetime.now(UTC)

        # Should be approximately 24 hours from now
        expected_min = before + timedelta(hours=24)
        expected_max = after + timedelta(hours=24)

        assert expected_min <= expires_at <= expected_max

    def test_create_expires_at_custom_hours(self) -> None:
        """Test create_expires_at with custom hours."""
        before = datetime.now(UTC)
        expires_at = m.EmailVerificationToken.create_expires_at(hours=12)
        after = datetime.now(UTC)

        # Should be approximately 12 hours from now
        expected_min = before + timedelta(hours=12)
        expected_max = after + timedelta(hours=12)

        assert expected_min <= expires_at <= expected_max

    def test_is_expired_false_for_future_expiration(self) -> None:
        """Test is_expired returns False for future expiration."""
        token = m.EmailVerificationToken(
            user_id=uuid4(),
            token_hash="test_token_hash",
            email="test@example.com",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        assert not token.is_expired

    def test_is_expired_true_for_past_expiration(self) -> None:
        """Test is_expired returns True for past expiration."""
        token = m.EmailVerificationToken(
            user_id=uuid4(),
            token_hash="test_token_hash",
            email="test@example.com",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )

        assert token.is_expired

    def test_is_used_false_when_used_at_is_none(self) -> None:
        """Test is_used returns False when used_at is None."""
        token = m.EmailVerificationToken(
            user_id=uuid4(),
            token_hash="test_token_hash",
            email="test@example.com",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used_at=None,
        )

        assert not token.is_used

    def test_is_used_true_when_used_at_is_set(self) -> None:
        """Test is_used returns True when used_at is set."""
        token = m.EmailVerificationToken(
            user_id=uuid4(),
            token_hash="test_token_hash",
            email="test@example.com",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used_at=datetime.now(UTC),
        )

        assert token.is_used

    def test_is_valid_true_when_not_expired_and_not_used(self) -> None:
        """Test is_valid returns True when token is not expired and not used."""
        token = m.EmailVerificationToken(
            user_id=uuid4(),
            token_hash="test_token_hash",
            email="test@example.com",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used_at=None,
        )

        assert token.is_valid

    def test_is_valid_false_when_expired(self) -> None:
        """Test is_valid returns False when token is expired."""
        token = m.EmailVerificationToken(
            user_id=uuid4(),
            token_hash="test_token_hash",
            email="test@example.com",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            used_at=None,
        )

        assert not token.is_valid

    def test_is_valid_false_when_used(self) -> None:
        """Test is_valid returns False when token is used."""
        token = m.EmailVerificationToken(
            user_id=uuid4(),
            token_hash="test_token_hash",
            email="test@example.com",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used_at=datetime.now(UTC),
        )

        assert not token.is_valid

    def test_is_valid_false_when_expired_and_used(self) -> None:
        """Test is_valid returns False when token is both expired and used."""
        token = m.EmailVerificationToken(
            user_id=uuid4(),
            token_hash="test_token_hash",
            email="test@example.com",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            used_at=datetime.now(UTC),
        )

        assert not token.is_valid
