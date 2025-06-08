# Authentication & Security

## Overview

The Litestar Fullstack SPA implements a comprehensive security system with multiple layers of protection. This includes JWT-based authentication, email verification, password reset flows, two-factor authentication (2FA), and configurable security policies.

## Authentication Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client (Browser)                       │
├─────────────────────────────────────────────────────────────┤
│                    JWT Token Storage                        │
│                 (HttpOnly Cookies/Memory)                   │
├─────────────────────────────────────────────────────────────┤
│                    API Requests with                        │
│                  Authorization Header                       │
└────────────────────────┬────────────────────────────────────┘
                        │
┌────────────────────────┴────────────────────────────────────┐
│                   JWT Middleware                            │
│              Token Validation & User Loading                │
├─────────────────────────────────────────────────────────────┤
│                  Route Guards                               │
│           Authorization & Permission Checks                 │
├─────────────────────────────────────────────────────────────┤
│                 Route Handlers                              │
│                Protected Endpoints                          │
└─────────────────────────────────────────────────────────────┘
```

## JWT Authentication

### Configuration

```python
from litestar.security.jwt import OAuth2PasswordBearerAuth
from app.server.security import current_user_from_token

auth = OAuth2PasswordBearerAuth[m.User](
    retrieve_user_handler=current_user_from_token,
    token_secret=settings.app.SECRET_KEY,
    token_url="/api/access/login",
    exclude=[
        # Public endpoints
        "/api/health",
        "/api/access/login",
        "/api/access/signup",
        "/api/access/forgot-password",
        "/api/access/reset-password",
        "/api/email-verification/*",
        # Documentation
        "^/schema",
        "^/public/",
    ],
)
```

### Token Generation

```python
from litestar.security.jwt import Token
from datetime import datetime, timedelta, UTC

def create_token(
    sub: str,
    exp: datetime | None = None,
    aud: str = "app:auth"
) -> str:
    """Create JWT token with claims."""
    if exp is None:
        exp = datetime.now(UTC) + timedelta(days=1)

    token = Token(
        sub=sub,  # User ID
        exp=exp,  # Expiration
        aud=aud,  # Audience
        iss="litestar-app",  # Issuer
    )

    return token.encode(
        secret=settings.app.SECRET_KEY,
        algorithm="HS256"
    )
```

### User Retrieval

```python
async def current_user_from_token(
    token: Token,
    connection: ASGIConnection[Any, Any, Any, Any]
) -> m.User | None:
    """Load user from JWT token."""
    try:
        user_id = UUID(token.sub)
    except ValueError:
        return None

    # Get user service from DI
    users_service = await anext(provide_users_service(connection))

    # Load user with relationships
    user = await users_service.get_one_or_none(
        id=user_id,
        is_active=True,
    )

    return user
```

## Authentication Flow

### User Registration

```python
@post(
    operation_id="Signup",
    path="/api/access/signup",
    exclude_from_auth=True
)
async def signup(
    self,
    data: UserSignup,
    users_service: UserService,
    email_verification_service: EmailVerificationTokenService,
) -> UserRead:
    """Register new user account."""
    # Validate password strength
    validate_password_strength(data.password)

    # Check if email exists
    existing = await users_service.get_one_or_none(email=data.email)
    if existing:
        raise ClientException("Email already registered")

    # Create user
    user = await users_service.create(
        data.model_dump(exclude={"password_confirm"})
    )

    # Send verification email
    if settings.auth.REQUIRE_EMAIL_VERIFICATION:
        token = await email_verification_service.create_verification_token(
            user_id=user.id,
            email=user.email
        )
        await email_service.send_verification_email(user, token)

    return UserRead.from_orm(user)
```

### Login with 2FA Support

```python
@post(
    operation_id="Login",
    path="/api/access/login",
    exclude_from_auth=True
)
async def login(
    self,
    data: OAuth2PasswordRequestForm,
    users_service: UserService,
    totp_service: TOTPService,
) -> LoginResponse:
    """Authenticate user with optional 2FA."""
    # Step 1: Verify credentials
    user = await users_service.authenticate(
        data.username,
        data.password
    )

    # Step 2: Check requirements
    auth_settings = get_settings().auth

    # Email verification check
    if auth_settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
        raise PermissionDeniedException("Email verification required")

    # 2FA check
    requires_2fa = False
    if auth_settings.ENABLE_2FA:
        # Required for certain roles
        if any(role.name in auth_settings.REQUIRE_2FA_FOR_ROLES
               for role in user.roles):
            requires_2fa = True
        # Or user enabled it
        elif user.has_2fa_enabled:
            requires_2fa = True

    if requires_2fa:
        # Generate temporary token for 2FA
        temp_token = create_token(
            sub=str(user.id),
            exp=datetime.now(UTC) + timedelta(minutes=5),
            aud="2fa-verify"
        )

        return LoginResponse(
            access_token=None,
            token_type="2fa_required",
            requires_2fa=True,
            temp_token=temp_token
        )

    # Generate full access token
    access_token = create_token(sub=str(user.id))

    # Update login tracking
    user.login_count += 1
    user.last_login_at = datetime.now(UTC)
    await users_service.repository.update(user)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        requires_2fa=False
    )
```

## Email Verification

### Token Model

```python
class EmailVerificationToken(UUIDAuditBase):
    """Email verification token model."""

    __tablename__ = "email_verification_token"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE")
    )
    email: Mapped[str] = mapped_column(String(255))
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True
    )
    expires_at: Mapped[datetime] = mapped_column()
    used_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None
    )

    # Relationships
    user: Mapped["User"] = relationship(lazy="selectin")
```

### Verification Service

```python
class EmailVerificationTokenService(
    service.SQLAlchemyAsyncRepositoryService[m.EmailVerificationToken]
):
    """Service for email verification."""

    async def create_verification_token(
        self,
        user_id: UUID,
        email: str
    ) -> m.EmailVerificationToken:
        """Create verification token."""
        # Expire existing tokens
        await self.repository.delete_where(
            m.EmailVerificationToken.user_id == user_id,
            m.EmailVerificationToken.used_at.is_(None),
        )

        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=24)

        return await self.repository.add(
            m.EmailVerificationToken(
                user_id=user_id,
                email=email,
                token=token,
                expires_at=expires_at,
            )
        )

    async def verify_token(self, token: str) -> m.EmailVerificationToken:
        """Verify and consume token."""
        db_obj = await self.repository.get_one_or_none(token=token)

        if db_obj is None:
            raise ClientException("Invalid verification token")

        if db_obj.used_at is not None:
            raise ClientException("Token already used")

        if db_obj.expires_at < datetime.now(UTC):
            raise ClientException("Token expired")

        # Mark as used
        db_obj.used_at = datetime.now(UTC)
        return await self.repository.update(db_obj)
```

### Verification Endpoint

```python
@Controller(path="/api/email-verification", exclude_from_auth=True)
class EmailVerificationController:
    """Email verification endpoints."""

    @post(operation_id="VerifyEmail", path="/verify")
    async def verify_email(
        self,
        data: EmailVerificationRequest,
        user_service: UserService,
        verification_service: EmailVerificationTokenService,
    ) -> EmailVerificationResponse:
        """Verify user's email address."""
        # Validate token
        token = await verification_service.verify_token(data.token)

        # Update user
        user = await user_service.verify_email(
            token.user_id,
            token.email
        )

        # Send welcome email
        await email_service.send_welcome_email(user)

        return EmailVerificationResponse(
            message="Email verified successfully",
            user_id=user.id,
            is_verified=True
        )
```

## Password Reset

### 🔒 Security Features

- Rate limiting (3 attempts per hour)
- IP address tracking
- User agent logging
- Time-limited tokens (1 hour)
- Single-use tokens

### Password Reset Service

```python
class PasswordResetService(
    service.SQLAlchemyAsyncRepositoryService[m.PasswordResetToken]
):
    """Password reset operations."""

    async def create_reset_token(
        self,
        user_id: UUID,
        ip_address: str = "unknown",
        user_agent: str = "unknown"
    ) -> m.PasswordResetToken:
        """Create password reset token."""
        # Check rate limit
        if await self.check_rate_limit(user_id):
            raise ClientException("Too many reset attempts")

        # Expire existing tokens
        await self.repository.delete_where(
            m.PasswordResetToken.user_id == user_id,
            m.PasswordResetToken.used_at.is_(None),
        )

        # Create new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        return await self.repository.add(
            m.PasswordResetToken(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )

    async def check_rate_limit(self, user_id: UUID) -> bool:
        """Check if user is rate limited."""
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        count = await self.repository.count(
            m.PasswordResetToken.user_id == user_id,
            m.PasswordResetToken.created_at > one_hour_ago,
        )
        return count >= 3
```

### Password Validation

```python
def validate_password_strength(password: str) -> None:
    """Validate password meets requirements."""
    if len(password) < 12:
        raise PasswordValidationError(
            "Password must be at least 12 characters"
        )

    if not any(c.isupper() for c in password):
        raise PasswordValidationError(
            "Password must contain uppercase letter"
        )

    if not any(c.islower() for c in password):
        raise PasswordValidationError(
            "Password must contain lowercase letter"
        )

    if not any(c.isdigit() for c in password):
        raise PasswordValidationError(
            "Password must contain digit"
        )

    special_chars = set("!@#$%^&*()_+-=[]{}|;:,.<>?")
    if not any(c in special_chars for c in password):
        raise PasswordValidationError(
            "Password must contain special character"
        )

    # Check common passwords
    common = {"password", "12345678", "qwerty", "abc123"}
    if password.lower() in common:
        raise PasswordValidationError("Password too common")
```

## Two-Factor Authentication (2FA)

### TOTP Implementation

```python
class TOTPService(
    service.SQLAlchemyAsyncRepositoryService[m.UserTOTPDevice]
):
    """TOTP-based 2FA service."""

    async def setup_totp(
        self,
        user_id: UUID,
        device_name: str
    ) -> tuple[UUID, str]:
        """Initialize TOTP setup."""
        # Generate secret
        secret = pyotp.random_base32()

        # Create inactive device
        device = await self.repository.add(
            m.UserTOTPDevice(
                user_id=user_id,
                name=device_name,
                secret=await self._encrypt_secret(secret),
                is_active=False
            )
        )

        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=settings.auth.TOTP_ISSUER
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_data = base64.b64encode(buffer.getvalue()).decode()

        return device.id, qr_data

    def _verify_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code."""
        totp = pyotp.TOTP(secret)
        # Allow 1 period drift
        return totp.verify(
            code,
            valid_window=settings.auth.TOTP_VALID_WINDOW
        )
```

### Backup Codes

```python
async def generate_backup_codes(
    self,
    user_id: UUID
) -> list[str]:
    """Generate single-use backup codes."""
    # Delete existing codes
    await self.backup_code_repo.delete_where(
        m.UserBackupCode.user_id == user_id
    )

    codes = []
    for _ in range(10):
        # Generate secure code
        code = ''.join(
            secrets.choice(string.digits)
            for _ in range(8)
        )

        # Store hashed version
        await self.backup_code_repo.add(
            m.UserBackupCode(
                user_id=user_id,
                code_hash=await crypt.get_password_hash(code)
            )
        )

        codes.append(code)

    return codes
```

## Authorization Guards

### Built-in Guards

```python
def requires_active_user(
    connection: ASGIConnection[Any, m.User, Token, Any],
    _: BaseRouteHandler
) -> None:
    """Require active user account."""
    if not connection.user.is_active:
        raise PermissionDeniedException("Account inactive")

def requires_verified_user(
    connection: ASGIConnection[Any, m.User, Token, Any],
    _: BaseRouteHandler
) -> None:
    """Require verified email."""
    if not connection.user.is_verified:
        raise PermissionDeniedException("Email verification required")

def requires_superuser(
    connection: ASGIConnection[Any, m.User, Token, Any],
    _: BaseRouteHandler
) -> None:
    """Require superuser privileges."""
    if not connection.user.is_superuser:
        raise PermissionDeniedException("Insufficient privileges")
```

### Team-Based Guards

```python
def requires_team_member(
    connection: ASGIConnection[Any, m.User, Token, Any],
    _: BaseRouteHandler
) -> None:
    """Require team membership."""
    team_id = connection.path_params.get("team_id")
    if not team_id:
        return

    # Check membership
    is_member = any(
        str(tm.team_id) == team_id
        for tm in connection.user.teams
    )

    if not is_member:
        raise PermissionDeniedException("Not a team member")

def requires_team_role(role: str):
    """Require specific team role."""
    def guard(
        connection: ASGIConnection[Any, m.User, Token, Any],
        _: BaseRouteHandler
    ) -> None:
        team_id = connection.path_params.get("team_id")
        if not team_id:
            return

        # Check role
        member = next(
            (tm for tm in connection.user.teams
             if str(tm.team_id) == team_id),
            None
        )

        if not member or member.role != role:
            raise PermissionDeniedException(
                f"Requires {role} role"
            )

    return guard
```

## Configurable Security

### Authentication Settings

```python
@dataclass
class AuthenticationSettings:
    """Configurable auth settings."""

    # Email verification
    REQUIRE_EMAIL_VERIFICATION: bool = field(
        default_factory=get_env("AUTH_REQUIRE_EMAIL_VERIFICATION", True)
    )

    # 2FA settings
    ENABLE_2FA: bool = field(
        default_factory=get_env("AUTH_ENABLE_2FA", True)
    )
    REQUIRE_2FA_FOR_ROLES: list[str] = field(
        default_factory=get_env(
            "AUTH_REQUIRE_2FA_FOR_ROLES",
            ["ADMIN", "SUPERUSER"]
        )
    )

    # Password policy
    PASSWORD_MIN_LENGTH: int = field(
        default_factory=get_env("AUTH_PASSWORD_MIN_LENGTH", 12)
    )
    PASSWORD_REQUIRE_UPPERCASE: bool = field(
        default_factory=get_env("AUTH_PASSWORD_REQUIRE_UPPERCASE", True)
    )
    PASSWORD_REQUIRE_SPECIAL: bool = field(
        default_factory=get_env("AUTH_PASSWORD_REQUIRE_SPECIAL", True)
    )

    # Security
    MAX_LOGIN_ATTEMPTS: int = field(
        default_factory=get_env("AUTH_MAX_LOGIN_ATTEMPTS", 5)
    )
    LOGIN_LOCKOUT_MINUTES: int = field(
        default_factory=get_env("AUTH_LOGIN_LOCKOUT_MINUTES", 30)
    )
```

### Environment-Based Configuration

```bash
# Development (.env.local)
AUTH_REQUIRE_EMAIL_VERIFICATION=false
AUTH_ENABLE_2FA=false
AUTH_PASSWORD_MIN_LENGTH=8

# Production (.env.production)
AUTH_REQUIRE_EMAIL_VERIFICATION=true
AUTH_ENABLE_2FA=true
AUTH_REQUIRE_2FA_FOR_ROLES=["ADMIN", "SUPERUSER"]
AUTH_PASSWORD_MIN_LENGTH=12
AUTH_MAX_LOGIN_ATTEMPTS=3
AUTH_LOGIN_LOCKOUT_MINUTES=60
```

## Security Best Practices

### 1. Input Validation

All inputs validated through msgspec:

```python
class UserLogin(msgspec.Struct):
    """Login request with validation."""
    email: str = msgspec.field(
        validator=lambda x: "@" in x and len(x) < 255
    )
    password: str = msgspec.field(
        validator=lambda x: 8 <= len(x) <= 128
    )
```

### 2. Rate Limiting

Implement for sensitive operations:

```python
from app.lib.rate_limit import rate_limit

@post("/api/access/login", exclude_from_auth=True)
@rate_limit(max_calls=5, period=60)  # 5 attempts per minute
async def login(...):
    ...
```

### 3. Security Headers

Configure security headers:

```python
from litestar.middleware import SecurityHeadersMiddleware

app = Litestar(
    middleware=[
        SecurityHeadersMiddleware(
            content_security_policy="default-src 'self'",
            strict_transport_security="max-age=31536000",
            x_content_type_options="nosniff",
            x_frame_options="DENY",
            x_xss_protection="1; mode=block",
        )
    ]
)
```

### 4. Secrets Management

Never hardcode secrets:

```python
# Bad
SECRET_KEY = "hardcoded-secret"

# Good
SECRET_KEY = os.environ["APP_SECRET_KEY"]
```

### 5. Audit Logging

Log security events:

```python
async def login(self, ...):
    """Login with audit logging."""
    try:
        user = await self.authenticate(...)
        logger.info(
            "Login successful",
            user_id=user.id,
            ip=request.client.host
        )
    except PermissionDeniedException:
        logger.warning(
            "Login failed",
            email=data.username,
            ip=request.client.host
        )
        raise
```

## Next Steps

Understanding authentication and security is crucial for:

1. Implementing new protected features
2. Configuring deployment environments
3. Conducting security audits

Continue to [Frontend Architecture](05-frontend-architecture.md) to see how authentication is handled on the client side.

---

*Security is not an afterthought but a core design principle. Every layer implements defense in depth to protect user data and system integrity.*
