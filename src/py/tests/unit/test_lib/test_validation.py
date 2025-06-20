"""Unit tests for validation utilities."""

import pytest

from app.lib.validation import (
    Email,
    Name,
    Password,
    PasswordValidationError,
    Phone,
    Slug,
    Url,
    Username,
    ValidationError,
    get_password_strength,
    validate_email,
    validate_name,
    validate_password,
    validate_password_strength,
    validate_phone,
    validate_slug,
    validate_url,
    validate_username,
)


class TestEmailValidation:
    """Test email validation functionality."""

    def test_valid_emails(self):
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "email.user@domain.org",
            "user+tag@example.co.uk",
            "firstname.lastname@example.com",
            "user123@example123.com",
        ]

        for email in valid_emails:
            result = validate_email(email)
            assert result == email.lower()

    def test_invalid_email_formats(self):
        """Test invalid email formats."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user..double.dot@example.com",
            "user@.example.com",
            "user@example.",
            "user name@example.com",  # space
            "user@ex ample.com",  # space in domain
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError, match="Invalid email format"):
                validate_email(email)

    def test_blocked_domains(self):
        """Test blocked email domains."""
        blocked_emails = [
            "user@10minutemail.com",
            "test@tempmail.org",
            "spam@guerrillamail.com",
            "fake@mailinator.com",
        ]

        for email in blocked_emails:
            with pytest.raises(ValidationError, match="Email domain not allowed"):
                validate_email(email)

    def test_blocked_patterns(self):
        """Test blocked email patterns."""
        blocked_emails = [
            "user+test@example.com",
            "user+spam@example.com",
            "test123@example.com",
            "noreply@example.com",
            "no-reply@example.com",
        ]

        for email in blocked_emails:
            with pytest.raises(ValidationError, match="Email format not allowed"):
                validate_email(email)

    def test_email_length_limits(self):
        """Test email length validation."""
        # Too short
        with pytest.raises(ValidationError, match="Email address too short"):
            validate_email("a@")

        # Too long
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValidationError, match="Email address too long"):
            validate_email(long_email)

        # Local part too long
        long_local = "a" * 70 + "@example.com"
        with pytest.raises(ValidationError, match="Email local part too long"):
            validate_email(long_local)

    def test_email_type_annotation(self):
        """Test Email type annotation works with msgspec."""
        # This would be tested in integration tests with actual msgspec usage


class TestPasswordValidation:
    """Test password validation functionality."""

    def test_valid_passwords(self):
        """Test valid passwords."""
        valid_passwords = [
            "MySecurePassword123!",
            "Another@Strong1Password",
            "Complex#Password2024",
            "VeryLong&SecurePassword123",
        ]

        for password in valid_passwords:
            result = validate_password(password)
            assert result == password

    def test_password_length_requirements(self):
        """Test password length validation."""
        # Too short
        with pytest.raises(PasswordValidationError, match="must be at least 12 characters"):
            validate_password_strength("Short1!")

        # Too long
        long_password = "A" * 130 + "1!"
        with pytest.raises(PasswordValidationError, match="must not exceed 128 characters"):
            validate_password_strength(long_password)

    def test_password_character_requirements(self):
        """Test password character requirements."""
        # Missing uppercase
        with pytest.raises(PasswordValidationError, match="uppercase letter"):
            validate_password_strength("lowercase123!")

        # Missing lowercase
        with pytest.raises(PasswordValidationError, match="lowercase letter"):
            validate_password_strength("UPPERCASE123!")

        # Missing digit
        with pytest.raises(PasswordValidationError, match="digit"):
            validate_password_strength("NoNumbersHere!")

        # Missing special character
        with pytest.raises(PasswordValidationError, match="special character"):
            validate_password_strength("NoSpecialChars123")

    def test_common_password_detection(self):
        """Test common password detection."""
        common_passwords = [
            "Qwerty123!Qwerty123!",  # Keyboard pattern, meets all requirements
        ]

        for password in common_passwords:
            with pytest.raises(PasswordValidationError, match="too common"):
                validate_password_strength(password)

    def test_password_strength_scoring(self):
        """Test password strength analysis."""
        # Weak password
        weak = get_password_strength("password")
        assert weak["strength"] == "weak"
        assert weak["score"] < 5

        # Medium password
        medium = get_password_strength("MyPassword123")
        assert medium["strength"] == "medium"
        assert 5 <= medium["score"] < 7

        # Strong password
        strong = get_password_strength("MyVerySecurePassword123!")
        assert strong["strength"] == "strong"
        assert strong["score"] >= 7

    def test_password_feedback(self):
        """Test password strength feedback."""
        analysis = get_password_strength("weak")
        assert len(analysis["feedback"]) > 0
        assert "Use at least 12 characters" in analysis["feedback"]


class TestNameValidation:
    """Test name validation functionality."""

    def test_valid_names(self):
        """Test valid names."""
        valid_names = [
            "John Doe",
            "María García",
            "O'Connor",
            "Jean-Pierre",
            "李明",  # Chinese characters
            "محمد",  # Arabic characters
            "José María",
            "Anne-Marie",
        ]

        for name in valid_names:
            result = validate_name(name)
            assert result == name.strip()

    def test_invalid_names(self):
        """Test invalid names."""
        # Empty name
        with pytest.raises(ValidationError, match="Name cannot be empty"):
            validate_name("")

        with pytest.raises(ValidationError, match="Name cannot be empty"):
            validate_name("   ")

        # Too long
        long_name = "A" * 101
        with pytest.raises(ValidationError, match="must not exceed 100 characters"):
            validate_name(long_name)

        # Invalid characters
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_name("John@Doe")

        with pytest.raises(ValidationError, match="invalid characters"):
            validate_name("John123")

        # Suspicious patterns
        with pytest.raises(ValidationError, match="suspicious patterns"):
            validate_name("Aaaaaa")  # 6 repeated characters

    def test_name_normalization(self):
        """Test name normalization."""
        # Multiple spaces
        result = validate_name("John   Doe")
        assert result == "John Doe"

        # Leading/trailing spaces
        result = validate_name("  John Doe  ")
        assert result == "John Doe"


class TestUsernameValidation:
    """Test username validation functionality."""

    def test_valid_usernames(self):
        """Test valid usernames."""
        valid_usernames = [
            "johndoe",
            "user123",
            "my-username",
            "user_name",
            "abc123def",
        ]

        for username in valid_usernames:
            result = validate_username(username)
            assert result == username.lower()

    def test_invalid_usernames(self):
        """Test invalid usernames."""
        # Too short
        with pytest.raises(ValidationError, match="at least 3 characters"):
            validate_username("ab")

        # Too long
        long_username = "a" * 31
        with pytest.raises(ValidationError, match="must not exceed 30 characters"):
            validate_username(long_username)

        # Invalid characters
        with pytest.raises(ValidationError, match="letters, numbers, hyphens, and underscores"):
            validate_username("user@name")

        with pytest.raises(ValidationError, match="letters, numbers, hyphens, and underscores"):
            validate_username("user name")

        # Must start with letter or number
        with pytest.raises(ValidationError, match="must start with a letter or number"):
            validate_username("-username")

        with pytest.raises(ValidationError, match="must start with a letter or number"):
            validate_username("_username")

    def test_reserved_usernames(self):
        """Test reserved username detection."""
        reserved_usernames = [
            "admin",
            "root",
            "api",
            "www",
            "support",
        ]

        for username in reserved_usernames:
            with pytest.raises(ValidationError, match="reserved and cannot be used"):
                validate_username(username)

    def test_username_abuse_patterns(self):
        """Test username abuse pattern detection."""
        with pytest.raises(ValidationError, match="too many repeated characters"):
            validate_username("aaaa")  # 4+ repeated characters


class TestUrlValidation:
    """Test URL validation functionality."""

    def test_valid_urls(self):
        """Test valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://subdomain.example.org",
            "https://example.com/path",
            "https://example.com/path?query=value",
            "https://example.com:8080/path",
        ]

        for url in valid_urls:
            result = validate_url(url)
            assert result == url

    def test_invalid_urls(self):
        """Test invalid URLs."""
        # No scheme
        with pytest.raises(ValidationError, match="must include a scheme"):
            validate_url("example.com")

        # Invalid scheme
        with pytest.raises(ValidationError, match="scheme must be one of"):
            validate_url("ftp://example.com")

        # No hostname
        with pytest.raises(ValidationError, match="must include a hostname"):
            validate_url("https://")

        # Blocked domains
        with pytest.raises(ValidationError, match="domain not allowed"):
            validate_url("https://localhost/path")

        with pytest.raises(ValidationError, match="domain not allowed"):
            validate_url("https://127.0.0.1/path")

        # Invalid scheme (will be caught as scheme error, not suspicious content)
        with pytest.raises(ValidationError, match="scheme must be one of"):
            validate_url("javascript:alert('xss')")

        # Test suspicious content in valid schemes
        with pytest.raises(ValidationError, match="suspicious content"):
            validate_url("https://example.com/javascript:alert")

    def test_url_length_limit(self):
        """Test URL length validation."""
        long_url = "https://example.com/" + "a" * 2048
        with pytest.raises(ValidationError, match="URL too long"):
            validate_url(long_url)


class TestSlugValidation:
    """Test slug validation functionality."""

    def test_valid_slugs(self):
        """Test valid slugs."""
        valid_slugs = [
            "my-slug",
            "article-title",
            "123-numbers",
            "simple",
            "multi-word-slug",
        ]

        for slug in valid_slugs:
            result = validate_slug(slug)
            assert result == slug.lower()

    def test_invalid_slugs(self):
        """Test invalid slugs."""
        # Empty
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_slug("")

        # Too long
        long_slug = "a" * 101
        with pytest.raises(ValidationError, match="must not exceed 100 characters"):
            validate_slug(long_slug)

        # Invalid characters
        with pytest.raises(ValidationError, match="lowercase letters, numbers, and hyphens"):
            validate_slug("slug_with_underscore")

        with pytest.raises(ValidationError, match="lowercase letters, numbers, and hyphens"):
            validate_slug("Slug With Spaces")

        # Cannot start/end with hyphen
        with pytest.raises(ValidationError, match="cannot start or end with a hyphen"):
            validate_slug("-slug")

        with pytest.raises(ValidationError, match="cannot start or end with a hyphen"):
            validate_slug("slug-")

        # Cannot have consecutive hyphens
        with pytest.raises(ValidationError, match="cannot contain consecutive hyphens"):
            validate_slug("slug--with--double")


class TestPhoneValidation:
    """Test phone validation functionality."""

    def test_valid_phones(self):
        """Test valid phone numbers."""
        valid_phones = [
            "+1-555-123-4567",
            "(555) 123-4567",
            "555.123.4567",
            "+44 20 1234 5678",
            "1234567",  # Minimum length
            "123456789012345",  # Maximum length
        ]

        for phone in valid_phones:
            result = validate_phone(phone)
            assert result == phone

    def test_invalid_phones(self):
        """Test invalid phone numbers."""
        # Empty
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_phone("")

        # Invalid format
        with pytest.raises(ValidationError, match="Invalid phone number format"):
            validate_phone("abc123")

        with pytest.raises(ValidationError, match="Invalid phone number format"):
            validate_phone("123-abc-4567")

        # Too short
        with pytest.raises(ValidationError, match="must be between 7 and 15 digits"):
            validate_phone("123456")  # Only 6 digits

        # Too long
        with pytest.raises(ValidationError, match="must be between 7 and 15 digits"):
            validate_phone("1234567890123456")  # 16 digits


class TestValidationFramework:
    """Test core validation framework functions."""

    def test_type_annotations(self):
        """Test that type annotations are properly defined."""
        # These would be tested in integration tests with msgspec
        assert Email is not None
        assert Password is not None
        assert Name is not None
        assert Username is not None
        assert Phone is not None
        assert Url is not None
        assert Slug is not None

    def test_validation_error_inheritance(self):
        """Test validation error inheritance."""
        from app.lib.exceptions import ApplicationClientError

        assert issubclass(ValidationError, ApplicationClientError)
        assert issubclass(PasswordValidationError, ValidationError)

    def test_non_string_inputs(self):
        """Test validation with non-string inputs."""
        validators = [
            validate_email,
            validate_password,
            validate_name,
            validate_username,
            validate_phone,
            validate_url,
            validate_slug,
        ]

        for validator in validators:
            with pytest.raises(ValidationError, match="must be a string"):
                validator(123)  # type: ignore

            with pytest.raises(ValidationError, match="must be a string"):
                validator(None)  # type: ignore
