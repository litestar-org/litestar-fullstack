"""Comprehensive tests for RefreshToken model."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.db import models as m
from tests.factories import RefreshTokenFactory

pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.models]


class TestRefreshTokenModel:
    """Test RefreshToken model properties and methods."""

    def test_is_expired_property_true(self) -> None:
        """Test is_expired property when token is expired."""
        token = RefreshTokenFactory.build(expires_at=datetime.now(UTC) - timedelta(hours=1))
        assert token.is_expired is True

    def test_is_expired_property_false(self) -> None:
        """Test is_expired property when token is not expired."""
        token = RefreshTokenFactory.build(expires_at=datetime.now(UTC) + timedelta(hours=1))
        assert token.is_expired is False

    def test_is_expired_at_exact_time(self) -> None:
        """Test is_expired at exact expiration time."""
        # Token expired exactly now
        token = RefreshTokenFactory.build(expires_at=datetime.now(UTC))
        # Should be considered expired or about to expire
        # The implementation likely uses <= so this should be True
        assert token.is_expired is True

    def test_is_revoked_property_true(self) -> None:
        """Test is_revoked property when token is revoked."""
        token = RefreshTokenFactory.build(revoked_at=datetime.now(UTC))
        assert token.is_revoked is True

    def test_is_revoked_property_false(self) -> None:
        """Test is_revoked property when token is not revoked."""
        token = RefreshTokenFactory.build(revoked_at=None)
        assert token.is_revoked is False

    def test_is_valid_property_true(self) -> None:
        """Test is_valid property when token is valid."""
        token = RefreshTokenFactory.build(
            expires_at=datetime.now(UTC) + timedelta(days=7),
            revoked_at=None,
        )
        assert token.is_valid is True

    def test_is_valid_property_false_expired(self) -> None:
        """Test is_valid property when token is expired."""
        token = RefreshTokenFactory.build(
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            revoked_at=None,
        )
        assert token.is_valid is False

    def test_is_valid_property_false_revoked(self) -> None:
        """Test is_valid property when token is revoked."""
        token = RefreshTokenFactory.build(
            expires_at=datetime.now(UTC) + timedelta(days=7),
            revoked_at=datetime.now(UTC),
        )
        assert token.is_valid is False

    def test_is_valid_property_false_both(self) -> None:
        """Test is_valid property when token is both expired and revoked."""
        token = RefreshTokenFactory.build(
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            revoked_at=datetime.now(UTC),
        )
        assert token.is_valid is False


class TestRefreshTokenCreation:
    """Test RefreshToken creation methods."""

    def test_create_expires_at_default(self) -> None:
        """Test create_expires_at with default 7 days."""
        before = datetime.now(UTC)
        expires_at = m.RefreshToken.create_expires_at()
        after = datetime.now(UTC)

        expected_min = before + timedelta(days=7)
        expected_max = after + timedelta(days=7)

        assert expected_min <= expires_at <= expected_max

    def test_create_expires_at_custom_days(self) -> None:
        """Test create_expires_at with custom days."""
        before = datetime.now(UTC)
        expires_at = m.RefreshToken.create_expires_at(days=14)
        after = datetime.now(UTC)

        expected_min = before + timedelta(days=14)
        expected_max = after + timedelta(days=14)

        assert expected_min <= expires_at <= expected_max

    def test_create_expires_at_short_duration(self) -> None:
        """Test create_expires_at with short duration (1 day)."""
        before = datetime.now(UTC)
        expires_at = m.RefreshToken.create_expires_at(days=1)
        after = datetime.now(UTC)

        expected_min = before + timedelta(days=1)
        expected_max = after + timedelta(days=1)

        assert expected_min <= expires_at <= expected_max


class TestRefreshTokenFamilyManagement:
    """Test RefreshToken family ID management."""

    def test_family_id_generation(self) -> None:
        """Test that family_id can be set."""
        family_id = uuid4()
        token = RefreshTokenFactory.build(family_id=family_id)
        assert token.family_id == family_id

    def test_different_tokens_same_family(self) -> None:
        """Test multiple tokens can belong to same family."""
        family_id = uuid4()
        token1 = RefreshTokenFactory.build(family_id=family_id)
        token2 = RefreshTokenFactory.build(family_id=family_id)

        assert token1.family_id == token2.family_id
        assert token1.id != token2.id

    def test_different_tokens_different_families(self) -> None:
        """Test tokens from different families."""
        token1 = RefreshTokenFactory.build(family_id=uuid4())
        token2 = RefreshTokenFactory.build(family_id=uuid4())

        assert token1.family_id != token2.family_id


class TestRefreshTokenMetadata:
    """Test RefreshToken metadata fields."""

    def test_device_info_field(self) -> None:
        """Test device_info field storage."""
        device_info = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        token = RefreshTokenFactory.build(device_info=device_info)
        assert token.device_info == device_info

    def test_device_info_with_ip(self) -> None:
        """Test device_info can include IP address."""
        device_info = "192.168.1.1 | Mozilla/5.0 Chrome/120"
        token = RefreshTokenFactory.build(device_info=device_info)
        assert token.device_info == device_info

    def test_device_info_with_ipv6(self) -> None:
        """Test device_info can include IPv6 address."""
        device_info = "2001:0db8:85a3::8a2e:0370:7334 | Firefox/121"
        token = RefreshTokenFactory.build(device_info=device_info)
        assert token.device_info == device_info

    def test_optional_device_info_field(self) -> None:
        """Test optional device_info field can be None."""
        token = RefreshTokenFactory.build(device_info=None)
        assert token.device_info is None


class TestRefreshTokenSecurityProperties:
    """Test security-related properties of RefreshToken."""

    def test_token_hash_is_stored(self) -> None:
        """Test that token_hash field exists and is set."""
        token = RefreshTokenFactory.build()
        assert token.token_hash is not None
        assert len(token.token_hash) > 0

    def test_token_hash_is_unique(self) -> None:
        """Test that different tokens have different hashes."""
        token1 = RefreshTokenFactory.build()
        token2 = RefreshTokenFactory.build()
        assert token1.token_hash != token2.token_hash

    def test_revocation_timestamp_precision(self) -> None:
        """Test that revocation timestamp has proper precision."""
        before_revoke = datetime.now(UTC)
        token = RefreshTokenFactory.build(revoked_at=before_revoke)

        assert token.revoked_at is not None
        assert token.revoked_at.tzinfo is not None  # Should be timezone-aware


class TestRefreshTokenRelationships:
    """Test RefreshToken relationships."""

    def test_user_id_relationship(self) -> None:
        """Test user_id foreign key relationship."""
        user_id = uuid4()
        token = RefreshTokenFactory.build(user_id=user_id)
        assert token.user_id == user_id

    def test_multiple_tokens_per_user(self) -> None:
        """Test user can have multiple tokens."""
        user_id = uuid4()
        tokens = [RefreshTokenFactory.build(user_id=user_id) for _ in range(5)]

        assert all(t.user_id == user_id for t in tokens)
        assert len(set(t.id for t in tokens)) == 5  # All unique IDs


class TestRefreshTokenStateTransitions:
    """Test state transitions for RefreshToken."""

    def test_valid_to_expired_transition(self) -> None:
        """Test transition from valid to expired state."""
        # Initially valid
        token = RefreshTokenFactory.build(
            expires_at=datetime.now(UTC) + timedelta(days=7),
            revoked_at=None,
        )
        assert token.is_valid is True

        # Simulate expiration by changing expires_at
        token.expires_at = datetime.now(UTC) - timedelta(hours=1)
        assert token.is_valid is False
        assert token.is_expired is True

    def test_valid_to_revoked_transition(self) -> None:
        """Test transition from valid to revoked state."""
        # Initially valid
        token = RefreshTokenFactory.build(
            expires_at=datetime.now(UTC) + timedelta(days=7),
            revoked_at=None,
        )
        assert token.is_valid is True

        # Revoke the token
        token.revoked_at = datetime.now(UTC)
        assert token.is_valid is False
        assert token.is_revoked is True
