"""Production-ready field validation utilities with comprehensive security checks."""

import hashlib
import re
import unicodedata
from typing import Annotated, Any
from urllib.parse import urlparse

import msgspec

from app.lib.exceptions import ApplicationClientError

EMAIL_BASIC_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]\.[a-zA-Z]{2,}$")
EMAIL_DOUBLE_DOT_PATTERN = re.compile(r"\.\.+")
EMAIL_BLOCKED_PATTERNS = [
    re.compile(r".*\+.*test.*@.*"),
    re.compile(r".*\+.*spam.*@.*"),
    re.compile(r"^test.*@.*"),
    re.compile(r"^noreply@.*"),
    re.compile(r"^no-reply@.*"),
]

PASSWORD_UPPERCASE_PATTERN = re.compile(r"[A-Z]")
PASSWORD_LOWERCASE_PATTERN = re.compile(r"[a-z]")
PASSWORD_DIGIT_PATTERN = re.compile(r"\d")
PASSWORD_SPECIAL_PATTERN = re.compile(r'[!@#$%^&*(),.?":{}|<>_+=\-\[\]\\\/~`]')
PASSWORD_COMMON_PATTERN = re.compile(r"(password|123456|qwerty|admin)", re.IGNORECASE)
PASSWORD_REPEATED_PATTERN = re.compile(r"(.)\1{4,}")
PASSWORD_SIMPLE_REPEATED_PATTERN = re.compile(r"^(.)\1{11,}$")
PASSWORD_SEQUENTIAL_PATTERN = re.compile(r"^(012|123|234|345|456|567|678|789|890|abc|bcd|cde)", re.IGNORECASE)
PASSWORD_KEYBOARD_PATTERN = re.compile(r"^(qwe|asd|zxc)", re.IGNORECASE)

NAME_WHITESPACE_PATTERN = re.compile(r"\s+")
NAME_VALID_PATTERN = re.compile(r"^[a-zA-ZÀ-ÿĀ-žА-я\u4e00-\u9fff\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff\s'\-\.]+$")
NAME_REPEATED_PATTERN = re.compile(r"(.)\1{4,}")

USERNAME_VALID_PATTERN = re.compile(r"^[a-z0-9_-]+$")
USERNAME_START_PATTERN = re.compile(r"^[a-z0-9]")
USERNAME_REPEATED_PATTERN = re.compile(r"(.)\1{3,}")

SLUG_VALID_PATTERN = re.compile(r"^[a-z0-9-]+$")

PHONE_BASIC_PATTERN = re.compile(r"^[\+]?[0-9\s\-\(\)\.]+$")
PHONE_DIGITS_PATTERN = re.compile(r"[^\d]")

EMAIL_BLOCKED_DOMAINS = {
    "10minutemail.com",
    "tempmail.org",
    "guerrillamail.com",
    "mailinator.com",
    "throwaway.email",
    "temp-mail.org",
    "yopmail.com",
    "maildrop.cc",
    "dispostable.com",
    "trashmail.com",
    "fake-mail.cf",
    "tempmail.net",
}

COMMON_PASSWORDS = {
    "password",
    "password123",
    "123456789",
    "qwertyuiop",
    "administrator",
    "welcome123",
    "password1234",
    "letmein123",
    "admin123456",
    "password12345",
}

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
PASSWORD_STRONG_LENGTH = 16
PASSWORD_VERY_STRONG_LENGTH = 20

PASSWORD_SCORE_STRONG = 7
PASSWORD_SCORE_MEDIUM = 5

PHONE_MIN_DIGITS = 7
PHONE_MAX_DIGITS = 15

EMAIL_MAX_LENGTH = 254
EMAIL_MIN_LENGTH = 3
EMAIL_LOCAL_PART_MAX_LENGTH = 64

NAME_MAX_LENGTH = 100
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30

URL_MAX_LENGTH = 2048
SLUG_MAX_LENGTH = 100

COMMON_PASSWORDS_HASHES = {
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
    "65e84be33532fb784c48129675f9eff3a682b27168c0ea744b2cf58ee02337c5",
    "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",
    "15e2b0d3c33891ebb0f1ef609ec419420c20e320ce94c65fbc8c3312448eb225",
    "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    "9af15b336e6a9619928537df30b2e6a2376569fcf9d7e773eccede65606529a0",
    "0b14d501a594442a01c6859541bcb3e8164d183d32937b851835442f69d5c94e",
    "e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446",
    "c775e7b757ede630cd0aa1113bd102661ab38829ca52a6422ab782862f268646",
}

RESERVED_USERNAMES = {
    "admin",
    "root",
    "api",
    "www",
    "mail",
    "ftp",
    "support",
    "help",
    "security",
    "privacy",
    "terms",
    "about",
    "contact",
    "blog",
    "news",
    "app",
    "application",
    "system",
    "test",
    "user",
    "guest",
    "demo",
    "null",
    "undefined",
    "none",
}

ALLOWED_URL_SCHEMES = {"http", "https"}
BLOCKED_URL_DOMAINS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",  # noqa: S104
    "::1",
    "[::1]",
}
SUSPICIOUS_URL_PATTERNS = ["javascript:", "data:", "vbscript:", "file:"]


class ValidationError(ApplicationClientError):
    """Custom validation error for all field validations.

    Inherits from ApplicationClientError for proper exception hierarchy integration.
    The exception_to_http_response handler converts this to HTTP 400 Bad Request.
    """


class PasswordValidationError(ValidationError):
    """Exception raised when password validation fails."""


def _ensure_str(value: Any, field_name: str, exc_type: type[ValidationError] = ValidationError) -> str:
    """Ensure the value is a string.

    Args:
        value: The value to validate.
        field_name: Field label used in error messages.
        exc_type: Exception type to raise on validation failure.

    Returns:
        The validated string.
    """
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise exc_type(msg)
    return value


def validate_not_empty(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        msg = "Value cannot be empty"
        raise ValidationError(msg)
    return cleaned


def validate_length(value: str, min_length: int = 0, max_length: int | None = None) -> str:
    if len(value) < min_length:
        msg = f"Must be at least {min_length} characters"
        raise ValidationError(msg)
    if max_length and len(value) > max_length:
        msg = f"Must not exceed {max_length} characters"
        raise ValidationError(msg)
    return value


def validate_no_control_chars(value: str) -> str:
    """Remove/reject control characters.

    Args:
        value: The string to validate.

    Raises:
        ValidationError: If control characters are found.

    Returns:
        The cleansed string without control characters.
    """
    if any(unicodedata.category(char) == "Cc" for char in value if char not in "\n\r\t"):
        msg = "Contains invalid control characters"
        raise ValidationError(msg)
    return value


def validate_password_strength(password: str) -> None:
    """Validate password meets production security requirements.

    Args:
        password: The password to validate.

    Raises:
        PasswordValidationError: If password doesn't meet requirements.
    """
    _ensure_str(password, "Password", PasswordValidationError)

    if len(password) < PASSWORD_MIN_LENGTH:
        msg = f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
        raise PasswordValidationError(msg)

    if len(password) > PASSWORD_MAX_LENGTH:
        msg = f"Password must not exceed {PASSWORD_MAX_LENGTH} characters"
        raise PasswordValidationError(msg)

    if not PASSWORD_UPPERCASE_PATTERN.search(password):
        msg = "Password must contain at least one uppercase letter"
        raise PasswordValidationError(msg)

    if not PASSWORD_LOWERCASE_PATTERN.search(password):
        msg = "Password must contain at least one lowercase letter"
        raise PasswordValidationError(msg)

    if not PASSWORD_DIGIT_PATTERN.search(password):
        msg = "Password must contain at least one digit"
        raise PasswordValidationError(msg)

    if not PASSWORD_SPECIAL_PATTERN.search(password):
        msg = "Password must contain at least one special character"
        raise PasswordValidationError(msg)

    if _is_common_password(password):
        msg = "Password is too common - please choose a more unique password"
        raise PasswordValidationError(msg)


def _is_common_password(password: str) -> bool:
    """Check if password is in common password list.

    Args:
        password: The password to check.

    Returns:
        True if the password is common, False otherwise.
    """
    password_lower = password.lower()

    if password_lower in COMMON_PASSWORDS:
        return True

    if PASSWORD_SIMPLE_REPEATED_PATTERN.match(password):
        return True

    if PASSWORD_SEQUENTIAL_PATTERN.match(password_lower):
        return True

    return bool(PASSWORD_KEYBOARD_PATTERN.match(password_lower))


def get_password_strength(password: str) -> dict[str, Any]:
    """Get detailed password strength analysis.

    Args:
        password: The password to analyze.

    Returns:
        Dictionary with strength analysis.
    """
    analysis: dict[str, Any] = {
        "score": 0,
        "strength": "weak",
        "requirements": {
            "length": len(password) >= PASSWORD_MIN_LENGTH,
            "uppercase": bool(PASSWORD_UPPERCASE_PATTERN.search(password)),
            "lowercase": bool(PASSWORD_LOWERCASE_PATTERN.search(password)),
            "digits": bool(PASSWORD_DIGIT_PATTERN.search(password)),
            "special_chars": bool(PASSWORD_SPECIAL_PATTERN.search(password)),
            "not_common": not _is_common_password(password),
        },
        "feedback": [],
    }

    if analysis["requirements"]["length"]:
        analysis["score"] += 2
    else:
        analysis["feedback"].append("Use at least 12 characters")

    if analysis["requirements"]["uppercase"]:
        analysis["score"] += 1
    else:
        analysis["feedback"].append("Include uppercase letters")

    if analysis["requirements"]["lowercase"]:
        analysis["score"] += 1
    else:
        analysis["feedback"].append("Include lowercase letters")

    if analysis["requirements"]["digits"]:
        analysis["score"] += 1
    else:
        analysis["feedback"].append("Include numbers")

    if analysis["requirements"]["special_chars"]:
        analysis["score"] += 1
    else:
        analysis["feedback"].append("Include special characters (!@#$%^&*)")

    if analysis["requirements"]["not_common"]:
        analysis["score"] += 1
    else:
        analysis["feedback"].append("Avoid common passwords")

    if len(password) >= PASSWORD_STRONG_LENGTH:
        analysis["score"] += 1
    if len(password) >= PASSWORD_VERY_STRONG_LENGTH:
        analysis["score"] += 1

    if analysis["score"] >= PASSWORD_SCORE_STRONG:
        analysis["strength"] = "strong"
    elif analysis["score"] >= PASSWORD_SCORE_MEDIUM:
        analysis["strength"] = "medium"
    else:
        analysis["strength"] = "weak"

    return analysis


def validate_email(v: str) -> str:
    """Production-ready email validation with comprehensive checks.

    Args:
        v: The email address to validate.

    Returns:
        The normalized email address.

    Raises:
        ValidationError: If validation fails.
    """
    v = _ensure_str(v, "Email")

    email = v.strip().lower()

    if len(email) > EMAIL_MAX_LENGTH:
        msg = "Email address too long"
        raise ValidationError(msg)

    if len(email) < EMAIL_MIN_LENGTH:
        msg = "Email address too short"
        raise ValidationError(msg)

    if not EMAIL_BASIC_PATTERN.match(email):
        msg = "Invalid email format"
        raise ValidationError(msg)

    if EMAIL_DOUBLE_DOT_PATTERN.search(email):
        msg = "Invalid email format"
        raise ValidationError(msg)

    local_part, _, domain = email.rpartition("@")
    if domain in EMAIL_BLOCKED_DOMAINS:
        msg = "Email domain not allowed"
        raise ValidationError(msg)

    for pattern in EMAIL_BLOCKED_PATTERNS:
        if pattern.match(email):
            msg = "Email format not allowed"
            raise ValidationError(msg)

    if len(local_part) > EMAIL_LOCAL_PART_MAX_LENGTH:
        msg = "Email local part too long"
        raise ValidationError(msg)

    return email


Email = Annotated[str, msgspec.Meta(description="Valid email address")]


def validate_password(v: str) -> str:
    """Production-ready password validation with security checks.

    Args:
        v: The password to validate.

    Returns:
        The validated password.

    Raises:
        ValidationError: If validation fails.
    """
    v = _ensure_str(v, "Password")

    validate_password_strength(v)

    password_hash = hashlib.sha256(v.encode()).hexdigest()
    if password_hash in COMMON_PASSWORDS_HASHES:
        msg = "Password is too common, please choose a different one"
        raise ValidationError(msg)

    return v


Password = Annotated[str, msgspec.Meta(description="Strong password (12+ chars, mixed case, numbers, symbols)")]


def validate_name(v: str) -> str:
    """Human name validation with proper handling of international names.

    Args:
        v: The name to validate.

    Returns:
        The normalized name.

    Raises:
        ValidationError: If validation fails.
    """
    v = _ensure_str(v, "Name")

    name = v.strip()
    name = NAME_WHITESPACE_PATTERN.sub(" ", name)

    if len(name) < 1:
        msg = "Name cannot be empty"
        raise ValidationError(msg)
    if len(name) > NAME_MAX_LENGTH:
        msg = f"Name must not exceed {NAME_MAX_LENGTH} characters"
        raise ValidationError(msg)

    if not NAME_VALID_PATTERN.match(name):
        msg = "Name contains invalid characters"
        raise ValidationError(msg)

    if NAME_REPEATED_PATTERN.search(name):
        msg = "Name contains suspicious patterns"
        raise ValidationError(msg)

    return name


def validate_username(v: str) -> str:
    """Username validation with uniqueness and character restrictions.

    Args:
        v: The username to validate.

    Returns:
        The normalized username.

    Raises:
        ValidationError: If validation fails.
    """
    v = _ensure_str(v, "Username")

    username = v.strip().lower()

    if len(username) < USERNAME_MIN_LENGTH:
        msg = f"Username must be at least {USERNAME_MIN_LENGTH} characters"
        raise ValidationError(msg)
    if len(username) > USERNAME_MAX_LENGTH:
        msg = f"Username must not exceed {USERNAME_MAX_LENGTH} characters"
        raise ValidationError(msg)

    if not USERNAME_VALID_PATTERN.match(username):
        msg = "Username can only contain letters, numbers, hyphens, and underscores"
        raise ValidationError(msg)

    if not USERNAME_START_PATTERN.match(username):
        msg = "Username must start with a letter or number"
        raise ValidationError(msg)

    if username in RESERVED_USERNAMES:
        msg = "Username is reserved and cannot be used"
        raise ValidationError(msg)

    if USERNAME_REPEATED_PATTERN.search(username):
        msg = "Username contains too many repeated characters"
        raise ValidationError(msg)

    return username


Name = Annotated[str, msgspec.Meta(description="Human name (1-100 characters)")]
Username = Annotated[str, msgspec.Meta(description="Username (3-30 characters, alphanumeric/hyphens/underscores)")]


def validate_url(v: str) -> str:
    """URL validation with security checks.

    Args:
        v: The URL to validate.

    Returns:
        The normalized URL.

    Raises:
        ValidationError: If validation fails.
    """
    v = _ensure_str(v, "URL")

    url = v.strip()

    if len(url) > URL_MAX_LENGTH:
        msg = "URL too long"
        raise ValidationError(msg)

    try:
        parsed = urlparse(url)
    except Exception as e:
        msg = "Invalid URL format"
        raise ValidationError(msg) from e

    if not parsed.scheme:
        msg = "URL must include a scheme (http:// or https://)"
        raise ValidationError(msg)

    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        msg = f"URL scheme must be one of: {', '.join(ALLOWED_URL_SCHEMES)}"
        raise ValidationError(msg)

    if not parsed.hostname:
        msg = "URL must include a hostname"
        raise ValidationError(msg)

    if parsed.hostname in BLOCKED_URL_DOMAINS:
        msg = "URL domain not allowed"
        raise ValidationError(msg)

    url_lower = url.lower()
    if any(suspicious in url_lower for suspicious in SUSPICIOUS_URL_PATTERNS):
        msg = "URL contains suspicious content"
        raise ValidationError(msg)

    return url


def validate_slug(v: str) -> str:
    """Slug validation for URL-safe identifiers.

    Args:
        v: The slug to validate.

    Returns:
        The normalized slug.

    Raises:
        ValidationError: If validation fails.
    """
    v = _ensure_str(v, "Slug")

    slug = v.strip().lower()

    if len(slug) < 1:
        msg = "Slug cannot be empty"
        raise ValidationError(msg)
    if len(slug) > SLUG_MAX_LENGTH:
        msg = f"Slug must not exceed {SLUG_MAX_LENGTH} characters"
        raise ValidationError(msg)

    if not SLUG_VALID_PATTERN.match(slug):
        msg = "Slug can only contain lowercase letters, numbers, and hyphens"
        raise ValidationError(msg)

    if slug.startswith("-") or slug.endswith("-"):
        msg = "Slug cannot start or end with a hyphen"
        raise ValidationError(msg)

    if "--" in slug:
        msg = "Slug cannot contain consecutive hyphens"
        raise ValidationError(msg)

    return slug


Url = Annotated[str, msgspec.Meta(description="Valid HTTP/HTTPS URL")]
Slug = Annotated[str, msgspec.Meta(description="URL-safe slug (lowercase, alphanumeric, hyphens)")]


def validate_phone(v: str) -> str:
    """International phone number validation.

    Args:
        v: The phone number to validate.

    Returns:
        The normalized phone number.

    Raises:
        ValidationError: If validation fails.
    """
    v = _ensure_str(v, "Phone number")

    phone = v.strip()

    if not phone:
        msg = "Phone number cannot be empty"
        raise ValidationError(msg)

    if not PHONE_BASIC_PATTERN.match(phone):
        msg = "Invalid phone number format"
        raise ValidationError(msg)

    digits_only = PHONE_DIGITS_PATTERN.sub("", phone)
    if len(digits_only) < PHONE_MIN_DIGITS or len(digits_only) > PHONE_MAX_DIGITS:
        msg = f"Phone number must be between {PHONE_MIN_DIGITS} and {PHONE_MAX_DIGITS} digits"
        raise ValidationError(msg)

    return phone


Phone = Annotated[str, msgspec.Meta(description="Valid international phone number")]
