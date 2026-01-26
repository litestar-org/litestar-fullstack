import pytest

from app.lib import validation


def test_validate_not_empty() -> None:
    assert validation.validate_not_empty("  test  ") == "test"
    with pytest.raises(validation.ValidationError, match="Value cannot be empty"):
        validation.validate_not_empty("   ")


def test_validate_length() -> None:
    assert validation.validate_length("abc", min_length=2, max_length=5) == "abc"
    with pytest.raises(validation.ValidationError, match="Must be at least 5 characters"):
        validation.validate_length("abc", min_length=5)
    with pytest.raises(validation.ValidationError, match="Must not exceed 2 characters"):
        validation.validate_length("abc", max_length=2)


def test_validate_no_control_chars() -> None:
    assert validation.validate_no_control_chars("hello\nworld") == "hello\nworld"
    with pytest.raises(validation.ValidationError, match="Contains invalid control characters"):
        validation.validate_no_control_chars("hello\x00world")


def test_validate_password_strength() -> None:
    # Valid strong password
    validation.validate_password_strength("StrongPass123!")

    # Too short
    with pytest.raises(validation.PasswordValidationError, match="at least 12 characters"):
        validation.validate_password_strength("Short1!")

    # No uppercase
    with pytest.raises(validation.PasswordValidationError, match="uppercase letter"):
        validation.validate_password_strength("weakpass123!")

    # No digit
    with pytest.raises(validation.PasswordValidationError, match="one digit"):
        validation.validate_password_strength("NoDigitsPass!")

    # No special
    with pytest.raises(validation.PasswordValidationError, match="special character"):
        validation.validate_password_strength("NoSpecialPass123")


def test_get_password_strength() -> None:
    result = validation.get_password_strength("StrongPass123!")
    assert result["strength"] == "strong"
    assert result["score"] >= 7

    result_weak = validation.get_password_strength("weak")
    assert result_weak["strength"] == "weak"
    assert result_weak["score"] < 5


def test_validate_email() -> None:
    assert validation.validate_email("valid@example.com") == "valid@example.com"
    assert validation.validate_email("VALID@EXAMPLE.COM") == "valid@example.com"

    with pytest.raises(validation.ValidationError, match="Invalid email format"):
        validation.validate_email("invalid-email")

    with pytest.raises(validation.ValidationError, match="domain not allowed"):
        validation.validate_email("test@10minutemail.com")
