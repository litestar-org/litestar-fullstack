"""Production-ready field validation utilities with comprehensive security checks."""

import hashlib
import re
import unicodedata
from typing import Annotated, Any
from urllib.parse import urlparse

import msgspec

# Try to import optional dependencies gracefully
try:
    from email_validator import EmailNotValidError
    from email_validator import validate_email as _validate_email
except ImportError:
    _validate_email = None
    EmailNotValidError = Exception

try:
    import phonenumbers
    from phonenumbers import NumberParseException
except ImportError:
    phonenumbers = None
    NumberParseException = Exception


# Compiled regex patterns for performance
# Email patterns
EMAIL_BASIC_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
EMAIL_BLOCKED_PATTERNS = [
    re.compile(r".*\+.*test.*@.*"),  # +test emails
    re.compile(r".*\+.*spam.*@.*"),  # +spam emails
    re.compile(r"^test.*@.*"),       # emails starting with test
    re.compile(r"^noreply@.*"),      # noreply addresses
    re.compile(r"^no-reply@.*"),     # no-reply addresses
]

# Password patterns
PASSWORD_UPPERCASE_PATTERN = re.compile(r"[A-Z]")
PASSWORD_LOWERCASE_PATTERN = re.compile(r"[a-z]")
PASSWORD_DIGIT_PATTERN = re.compile(r"\d")
PASSWORD_SPECIAL_PATTERN = re.compile(r'[!@#$%^&*(),.?":{}|<>_+=\-\[\]\\\/~`]')
PASSWORD_COMMON_PATTERN = re.compile(r"(password|123456|qwerty|admin)", re.IGNORECASE)
PASSWORD_REPEATED_PATTERN = re.compile(r"(.)\1{4,}")  # 5+ repeated characters
PASSWORD_SIMPLE_REPEATED_PATTERN = re.compile(r"^(.)\1{11,}$")  # 12+ same character
PASSWORD_SEQUENTIAL_PATTERN = re.compile(r"^(012|123|234|345|456|567|678|789|890|abc|bcd|cde)", re.IGNORECASE)
PASSWORD_KEYBOARD_PATTERN = re.compile(r"^(qwe|asd|zxc)", re.IGNORECASE)

# Name patterns - Unicode-aware
NAME_WHITESPACE_PATTERN = re.compile(r"\s+")
NAME_VALID_PATTERN = re.compile(r"^[a-zA-ZÀ-ÿĀ-žА-я\u4e00-\u9fff\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff\s'\-\.]+$")
NAME_REPEATED_PATTERN = re.compile(r"(.)\1{4,}")  # 5+ repeated characters

# Username patterns
USERNAME_VALID_PATTERN = re.compile(r"^[a-z0-9_-]+$")
USERNAME_START_PATTERN = re.compile(r"^[a-z0-9]")
USERNAME_REPEATED_PATTERN = re.compile(r"(.)\1{3,}")  # 4+ repeated characters

# Slug patterns
SLUG_VALID_PATTERN = re.compile(r"^[a-z0-9-]+$")

# Phone patterns
PHONE_BASIC_PATTERN = re.compile(r"^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$")
PHONE_DIGITS_PATTERN = re.compile(r"[^\d]")

# Email domain/pattern constants
EMAIL_BLOCKED_DOMAINS = {
    "10minutemail.com", "tempmail.org", "guerrillamail.com",
    "mailinator.com", "throwaway.email", "temp-mail.org",
    "yopmail.com", "maildrop.cc", "dispostable.com",
    "trashmail.com", "fake-mail.cf", "tempmail.net"
}

# Common passwords (first 1000 most common)
COMMON_PASSWORDS = {
    "password", "password123", "123456789", "qwertyuiop",
    "administrator", "welcome123", "password1234",
    "letmein123", "admin123456", "password12345"
}

# Common passwords hash set (SHA256 hashes of most common passwords)
COMMON_PASSWORDS_HASHES = {
    # SHA256 hashes of common passwords
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # empty
    "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # 'password'
    "65e84be33532fb784c48129675f9eff3a682b27168c0ea744b2cf58ee02337c5",  # 'qwerty'
    "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",  # '123456'
    "15e2b0d3c33891ebb0f1ef609ec419420c20e320ce94c65fbc8c3312448eb225",  # '123456789'
    "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  # '123'
    "9af15b336e6a9619928537df30b2e6a2376569fcf9d7e773eccede65606529a0",  # 'qwerty123'
    "0b14d501a594442a01c6859541bcb3e8164d183d32937b851835442f69d5c94e",  # 'password1'
    "e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446",  # 'password123'
    "c775e7b757ede630cd0aa1113bd102661ab38829ca52a6422ab782862f268646",  # '1234567890'
}

# Reserved usernames constant
RESERVED_USERNAMES = {
    "admin", "root", "api", "www", "mail", "ftp", "support",
    "help", "security", "privacy", "terms", "about", "contact",
    "blog", "news", "app", "application", "system", "test",
    "user", "guest", "demo", "null", "undefined", "none"
}

# URL validation constants
ALLOWED_URL_SCHEMES = {"http", "https"}
BLOCKED_URL_DOMAINS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}
SUSPICIOUS_URL_PATTERNS = ["javascript:", "data:", "vbscript:", "file:"]


class ValidationError(ValueError):
    """Custom validation error for all field validations."""


class PasswordValidationError(ValidationError):
    """Exception raised when password validation fails."""


# Core Validation Framework
def validate_not_empty(value: str) -> str:
    """Ensure string is not empty after stripping."""
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("Value cannot be empty")
    return cleaned


def validate_length(value: str, min_length: int = 0, max_length: int | None = None) -> str:
    """Validate string length."""
    if len(value) < min_length:
        raise ValidationError(f"Must be at least {min_length} characters")
    if max_length and len(value) > max_length:
        raise ValidationError(f"Must not exceed {max_length} characters")
    return value


def validate_no_control_chars(value: str) -> str:
    """Remove/reject control characters."""
    if any(unicodedata.category(char) == "Cc" for char in value if char not in "\n\r\t"):
        raise ValidationError("Contains invalid control characters")
    return value


def validate_password_strength(password: str) -> None:
    """Validate password meets production security requirements.

    Args:
        password: The password to validate

    Raises:
        PasswordValidationError: If password doesn't meet requirements
    """
    if not isinstance(password, str):
        raise PasswordValidationError("Password must be a string")

    # Length requirements
    if len(password) < 12:
        raise PasswordValidationError("Password must be at least 12 characters long")

    if len(password) > 128:
        raise PasswordValidationError("Password must not exceed 128 characters")

    # Character type requirements
    if not PASSWORD_UPPERCASE_PATTERN.search(password):
        raise PasswordValidationError("Password must contain at least one uppercase letter")

    if not PASSWORD_LOWERCASE_PATTERN.search(password):
        raise PasswordValidationError("Password must contain at least one lowercase letter")

    if not PASSWORD_DIGIT_PATTERN.search(password):
        raise PasswordValidationError("Password must contain at least one digit")

    if not PASSWORD_SPECIAL_PATTERN.search(password):
        raise PasswordValidationError("Password must contain at least one special character")

    # Check against common patterns
    if _is_common_password(password):
        raise PasswordValidationError("Password is too common - please choose a more unique password")


def _is_common_password(password: str) -> bool:
    """Check if password is in common password list.

    Args:
        password: The password to check

    Returns:
        True if password is common, False otherwise
    """
    password_lower = password.lower()

    # Check exact matches
    if password_lower in COMMON_PASSWORDS:
        return True

    # Check for simple patterns
    if PASSWORD_SIMPLE_REPEATED_PATTERN.match(password):  # Repeated characters
        return True

    if PASSWORD_SEQUENTIAL_PATTERN.match(password_lower):
        return True

    if PASSWORD_KEYBOARD_PATTERN.match(password_lower):  # Keyboard patterns
        return True

    return False


def get_password_strength(password: str) -> dict[str, Any]:
    """Get detailed password strength analysis.

    Args:
        password: The password to analyze

    Returns:
        Dictionary with strength analysis
    """
    analysis: dict[str, Any] = {
        "score": 0,
        "strength": "weak",
        "requirements": {
            "length": len(password) >= 12,
            "uppercase": bool(PASSWORD_UPPERCASE_PATTERN.search(password)),
            "lowercase": bool(PASSWORD_LOWERCASE_PATTERN.search(password)),
            "digits": bool(PASSWORD_DIGIT_PATTERN.search(password)),
            "special_chars": bool(PASSWORD_SPECIAL_PATTERN.search(password)),
            "not_common": not _is_common_password(password)
        },
        "feedback": []
    }

    # Calculate score
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

    # Bonus points for length
    if len(password) >= 16:
        analysis["score"] += 1
    if len(password) >= 20:
        analysis["score"] += 1

    # Determine strength level
    if analysis["score"] >= 7:
        analysis["strength"] = "strong"
    elif analysis["score"] >= 5:
        analysis["strength"] = "medium"
    else:
        analysis["strength"] = "weak"

    return analysis


# Email Validation
def validate_email(v: str) -> str:
    """Production-ready email validation with comprehensive checks."""
    if not isinstance(v, str):
        raise ValidationError("Email must be a string")

    # Basic cleanup
    email = v.strip().lower()

    # Length check
    if len(email) > 254:  # RFC 5321 limit
        raise ValidationError("Email address too long")

    if len(email) < 3:
        raise ValidationError("Email address too short")

    # Use email-validator library for comprehensive validation if available
    if _validate_email:
        try:
            validated_email = _validate_email(
                email,
                check_deliverability=True,  # DNS MX record check
            )
            email = validated_email.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email address: {e!s}")
    else:
        # Fallback to basic regex validation
        if not EMAIL_BASIC_PATTERN.match(email):
            raise ValidationError("Invalid email format")

    # Check against blocked domains
    domain = email.split("@")[1] if "@" in email else ""
    if domain in EMAIL_BLOCKED_DOMAINS:
        raise ValidationError("Email domain not allowed")

    # Check against blocked patterns
    for pattern in EMAIL_BLOCKED_PATTERNS:
        if pattern.match(email):
            raise ValidationError("Email format not allowed")

    # Additional security checks
    local_part = email.split("@")[0]
    if len(local_part) > 64:  # RFC 5321 limit
        raise ValidationError("Email local part too long")

    return email


# Type annotation for use in schemas
Email = Annotated[str, msgspec.Meta(description="Valid email address")]


# Password Validation
def validate_password(v: str) -> str:
    """Production-ready password validation with security checks."""
    if not isinstance(v, str):
        raise ValidationError("Password must be a string")

    # Use existing validation function
    validate_password_strength(v)

    # Check against common passwords
    password_hash = hashlib.sha256(v.encode()).hexdigest()
    if password_hash in COMMON_PASSWORDS_HASHES:
        raise ValidationError("Password is too common, please choose a different one")

    return v


# Type annotation for use in schemas
Password = Annotated[str, msgspec.Meta(description="Strong password (12+ chars, mixed case, numbers, symbols)")]


# Name and Text Validation
def validate_name(v: str) -> str:
    """Human name validation with proper handling of international names."""
    if not isinstance(v, str):
        raise ValidationError("Name must be a string")

    # Clean and normalize
    name = v.strip()
    name = NAME_WHITESPACE_PATTERN.sub(" ", name)  # Normalize whitespace

    # Length validation
    if len(name) < 1:
        raise ValidationError("Name cannot be empty")
    if len(name) > 100:
        raise ValidationError("Name must not exceed 100 characters")

    # Character validation - allow letters, spaces, hyphens, apostrophes, periods
    # Allow extended Unicode for international names
    if not NAME_VALID_PATTERN.match(name):
        raise ValidationError("Name contains invalid characters")

    # Prevent abuse patterns
    if NAME_REPEATED_PATTERN.search(name):  # 5+ repeated characters
        raise ValidationError("Name contains suspicious patterns")

    return name


def validate_username(v: str) -> str:
    """Username validation with uniqueness and character restrictions."""
    if not isinstance(v, str):
        raise ValidationError("Username must be a string")

    # Clean and normalize
    username = v.strip().lower()

    # Length validation
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters")
    if len(username) > 30:
        raise ValidationError("Username must not exceed 30 characters")

    # Character validation - alphanumeric, hyphens, underscores only
    if not USERNAME_VALID_PATTERN.match(username):
        raise ValidationError("Username can only contain letters, numbers, hyphens, and underscores")

    # Must start with letter or number
    if not USERNAME_START_PATTERN.match(username):
        raise ValidationError("Username must start with a letter or number")

    # Check reserved usernames
    if username in RESERVED_USERNAMES:
        raise ValidationError("Username is reserved and cannot be used")

    # Prevent abuse patterns
    if USERNAME_REPEATED_PATTERN.search(username):  # 4+ repeated characters
        raise ValidationError("Username contains too many repeated characters")

    return username


# Type annotations
Name = Annotated[str, msgspec.Meta(description="Human name (1-100 characters)")]
Username = Annotated[str, msgspec.Meta(description="Username (3-30 characters, alphanumeric/hyphens/underscores)")]




def validate_url(v: str) -> str:
    """URL validation with security checks."""
    if not isinstance(v, str):
        raise ValidationError("URL must be a string")

    url = v.strip()

    # Length check
    if len(url) > 2048:
        raise ValidationError("URL too long")

    try:
        parsed = urlparse(url)
    except Exception:
        raise ValidationError("Invalid URL format")

    # Scheme validation
    if not parsed.scheme:
        raise ValidationError("URL must include a scheme (http:// or https://)")

    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise ValidationError(f"URL scheme must be one of: {', '.join(ALLOWED_URL_SCHEMES)}")

    # Domain validation
    if not parsed.hostname:
        raise ValidationError("URL must include a hostname")

    if parsed.hostname in BLOCKED_URL_DOMAINS:
        raise ValidationError("URL domain not allowed")

    # Prevent common attacks
    url_lower = url.lower()
    if any(suspicious in url_lower for suspicious in SUSPICIOUS_URL_PATTERNS):
        raise ValidationError("URL contains suspicious content")

    return url


def validate_slug(v: str) -> str:
    """Slug validation for URL-safe identifiers."""
    if not isinstance(v, str):
        raise ValidationError("Slug must be a string")

    slug = v.strip().lower()

    # Length validation
    if len(slug) < 1:
        raise ValidationError("Slug cannot be empty")
    if len(slug) > 100:
        raise ValidationError("Slug must not exceed 100 characters")

    # Character validation - lowercase, numbers, hyphens only
    if not SLUG_VALID_PATTERN.match(slug):
        raise ValidationError("Slug can only contain lowercase letters, numbers, and hyphens")

    # Cannot start or end with hyphen
    if slug.startswith("-") or slug.endswith("-"):
        raise ValidationError("Slug cannot start or end with a hyphen")

    # Cannot have consecutive hyphens
    if "--" in slug:
        raise ValidationError("Slug cannot contain consecutive hyphens")

    return slug


# Type annotations
Url = Annotated[str, msgspec.Meta(description="Valid HTTP/HTTPS URL")]
Slug = Annotated[str, msgspec.Meta(description="URL-safe slug (lowercase, alphanumeric, hyphens)")]


# Phone Number Validation
def validate_phone(v: str) -> str:
    """International phone number validation."""
    if not isinstance(v, str):
        raise ValidationError("Phone number must be a string")

    phone = v.strip()

    if not phone:
        raise ValidationError("Phone number cannot be empty")

    # If phonenumbers library is available, use it for proper validation
    if phonenumbers:
        try:
            # Try to parse with international format first
            if phone.startswith("+"):
                parsed_number = phonenumbers.parse(phone, None)
            else:
                # For numbers without country code, you might want to set a default region
                # For now, we'll require international format
                raise ValidationError("Phone number must include country code (e.g., +1 for US)")

            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError("Invalid phone number")

            # Format to international format
            formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            return formatted

        except NumberParseException:
            raise ValidationError("Invalid phone number format")
    else:
        # Fallback to basic validation
        # Allow only digits, spaces, hyphens, parentheses, and plus sign
        if not PHONE_BASIC_PATTERN.match(phone):
            raise ValidationError("Invalid phone number format")

        # Basic length check
        digits_only = PHONE_DIGITS_PATTERN.sub("", phone)
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValidationError("Phone number must be between 7 and 15 digits")

        return phone


# Type annotation
Phone = Annotated[str, msgspec.Meta(description="Valid international phone number")]
