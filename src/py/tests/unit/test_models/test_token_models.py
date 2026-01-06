"""Unit tests for token model properties.

These tests verify model property logic without database interaction.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.db import models as m
from tests.factories import EmailVerificationTokenFactory, PasswordResetTokenFactory

pytestmark = [pytest.mark.unit, pytest.mark.auth]


# -----------------------------------------------------------------------------
# EmailVerificationToken model property tests
# -----------------------------------------------------------------------------


def test_email_verification_token_is_expired_true() -> None:
    """Test is_expired property when token is expired."""
    token = EmailVerificationTokenFactory.build(expires_at=datetime.now(UTC) - timedelta(hours=1))
    assert token.is_expired is True


def test_email_verification_token_is_expired_false() -> None:
    """Test is_expired property when token is not expired."""
    token = EmailVerificationTokenFactory.build(expires_at=datetime.now(UTC) + timedelta(hours=1))
    assert token.is_expired is False


def test_email_verification_token_is_used_true() -> None:
    """Test is_used property when token is used."""
    token = EmailVerificationTokenFactory.build(used_at=datetime.now(UTC))
    assert token.is_used is True


def test_email_verification_token_is_used_false() -> None:
    """Test is_used property when token is not used."""
    token = EmailVerificationTokenFactory.build(used_at=None)
    assert token.is_used is False


def test_email_verification_token_is_valid_true() -> None:
    """Test is_valid property when token is valid."""
    token = EmailVerificationTokenFactory.build(expires_at=datetime.now(UTC) + timedelta(hours=1), used_at=None)
    assert token.is_valid is True


def test_email_verification_token_is_valid_false_expired() -> None:
    """Test is_valid property when token is expired."""
    token = EmailVerificationTokenFactory.build(expires_at=datetime.now(UTC) - timedelta(hours=1), used_at=None)
    assert token.is_valid is False


def test_email_verification_token_is_valid_false_used() -> None:
    """Test is_valid property when token is used."""
    token = EmailVerificationTokenFactory.build(
        expires_at=datetime.now(UTC) + timedelta(hours=1), used_at=datetime.now(UTC)
    )
    assert token.is_valid is False


def test_email_verification_token_create_expires_at_default() -> None:
    """Test create_expires_at with default 24 hours."""
    before = datetime.now(UTC)
    expires_at = m.EmailVerificationToken.create_expires_at()
    after = datetime.now(UTC)

    expected_min = before + timedelta(hours=24)
    expected_max = after + timedelta(hours=24)

    assert expected_min <= expires_at <= expected_max


def test_email_verification_token_create_expires_at_custom_hours() -> None:
    """Test create_expires_at with custom hours."""
    before = datetime.now(UTC)
    expires_at = m.EmailVerificationToken.create_expires_at(hours=12)
    after = datetime.now(UTC)

    expected_min = before + timedelta(hours=12)
    expected_max = after + timedelta(hours=12)

    assert expected_min <= expires_at <= expected_max


# -----------------------------------------------------------------------------
# PasswordResetToken model property tests
# -----------------------------------------------------------------------------


def test_password_reset_token_is_expired_true() -> None:
    """Test is_expired property when token is expired."""
    token = PasswordResetTokenFactory.build(expires_at=datetime.now(UTC) - timedelta(hours=1))
    assert token.is_expired is True


def test_password_reset_token_is_expired_false() -> None:
    """Test is_expired property when token is not expired."""
    token = PasswordResetTokenFactory.build(expires_at=datetime.now(UTC) + timedelta(hours=1))
    assert token.is_expired is False


def test_password_reset_token_is_used_true() -> None:
    """Test is_used property when token is used."""
    token = PasswordResetTokenFactory.build(used_at=datetime.now(UTC))
    assert token.is_used is True


def test_password_reset_token_is_used_false() -> None:
    """Test is_used property when token is not used."""
    token = PasswordResetTokenFactory.build(used_at=None)
    assert token.is_used is False


def test_password_reset_token_is_valid_true() -> None:
    """Test is_valid property when token is valid."""
    token = PasswordResetTokenFactory.build(expires_at=datetime.now(UTC) + timedelta(hours=1), used_at=None)
    assert token.is_valid is True


def test_password_reset_token_is_valid_false_expired() -> None:
    """Test is_valid property when token is expired."""
    token = PasswordResetTokenFactory.build(expires_at=datetime.now(UTC) - timedelta(hours=1), used_at=None)
    assert token.is_valid is False


def test_password_reset_token_is_valid_false_used() -> None:
    """Test is_valid property when token is used."""
    token = PasswordResetTokenFactory.build(
        expires_at=datetime.now(UTC) + timedelta(hours=1), used_at=datetime.now(UTC)
    )
    assert token.is_valid is False


def test_password_reset_token_create_expires_at_default() -> None:
    """Test create_expires_at with default 1 hour."""
    before = datetime.now(UTC)
    expires_at = m.PasswordResetToken.create_expires_at()
    after = datetime.now(UTC)

    expected_min = before + timedelta(hours=1)
    expected_max = after + timedelta(hours=1)

    assert expected_min <= expires_at <= expected_max


def test_password_reset_token_create_expires_at_custom_hours() -> None:
    """Test create_expires_at with custom hours."""
    before = datetime.now(UTC)
    expires_at = m.PasswordResetToken.create_expires_at(hours=2)
    after = datetime.now(UTC)

    expected_min = before + timedelta(hours=2)
    expected_max = after + timedelta(hours=2)

    assert expected_min <= expires_at <= expected_max
