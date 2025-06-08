# Two-Factor Authentication (2FA) with TOTP Implementation

## Overview

Implement a comprehensive 2FA system using Time-based One-Time Passwords (TOTP) with configurable authentication settings.

## Goals

1. **TOTP-based 2FA**: Implement industry-standard TOTP (RFC 6238) for secure two-factor authentication
2. **Configurable Authentication**: Make authentication requirements configurable via settings
3. **User-Friendly Setup**: Provide QR codes and backup codes for easy setup
4. **Security First**: Ensure secure implementation with proper validation and rate limiting

## Implementation Steps

### Phase 1: Database Models & Settings

1. **Create 2FA Models**
   - `UserTOTPDevice`: Store TOTP secrets and device info
   - `UserBackupCode`: Store encrypted backup codes
   - `UserAuthAttempt`: Track authentication attempts for rate limiting

2. **Authentication Settings**
   ```python
   @dataclass
   class AuthSettings:
       # Email verification
       REQUIRE_EMAIL_VERIFICATION: bool = True
       EMAIL_VERIFICATION_TIMEOUT_HOURS: int = 24

       # 2FA settings
       ENABLE_2FA: bool = True
       REQUIRE_2FA_FOR_ADMIN: bool = True
       OPTIONAL_2FA_FOR_USERS: bool = True

       # TOTP settings
       TOTP_ISSUER: str = "Litestar App"
       TOTP_ALGORITHM: str = "SHA1"
       TOTP_DIGITS: int = 6
       TOTP_INTERVAL: int = 30

       # Security settings
       MAX_LOGIN_ATTEMPTS: int = 5
       LOGIN_LOCKOUT_MINUTES: int = 30
       BACKUP_CODES_COUNT: int = 10

       # Session settings
       REQUIRE_FRESH_LOGIN_FOR_SENSITIVE: bool = True
       FRESH_LOGIN_TIMEOUT_MINUTES: int = 15
   ```

### Phase 2: Service Layer

1. **TOTPService**
   - Generate TOTP secrets
   - Generate QR codes for authenticator apps
   - Validate TOTP codes
   - Handle backup codes

2. **Enhanced UserService**
   - Check 2FA requirements
   - Validate authentication flow
   - Track login attempts
   - Handle account lockouts

### Phase 3: API Endpoints

1. **2FA Setup Endpoints**
   - `POST /api/2fa/setup/init`: Initialize 2FA setup
   - `POST /api/2fa/setup/verify`: Verify TOTP and enable 2FA
   - `GET /api/2fa/setup/qr`: Get QR code for authenticator
   - `POST /api/2fa/backup-codes`: Generate new backup codes

2. **2FA Authentication Endpoints**
   - `POST /api/access/login` (enhanced): Return 2FA required flag
   - `POST /api/2fa/verify`: Verify TOTP code after password login
   - `POST /api/2fa/verify-backup`: Use backup code

3. **2FA Management Endpoints**
   - `GET /api/2fa/status`: Get 2FA status for user
   - `DELETE /api/2fa/disable`: Disable 2FA (requires password)
   - `GET /api/2fa/devices`: List trusted devices

### Phase 4: Frontend Components

1. **2FA Setup Flow**
   - Setup wizard component
   - QR code display
   - Backup codes display/download
   - Test verification step

2. **2FA Login Flow**
   - TOTP input component
   - Backup code option
   - Remember device option
   - Error handling

3. **2FA Management**
   - Settings page integration
   - Enable/disable 2FA
   - Regenerate backup codes
   - View trusted devices

## Technical Details

### TOTP Implementation

```python
import pyotp
import qrcode
from io import BytesIO
import base64

class TOTPService:
    async def generate_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()

    async def generate_qr_code(self, user: User, secret: str) -> str:
        """Generate QR code for authenticator apps."""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=self.settings.TOTP_ISSUER
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        return base64.b64encode(buffer.getvalue()).decode()

    async def verify_code(self, secret: str, code: str) -> bool:
        """Verify a TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
```

### Authentication Flow

```python
# Enhanced login flow
async def login(self, username: str, password: str) -> LoginResponse:
    # 1. Verify password
    user = await self.authenticate(username, password)

    # 2. Check if email verification required
    if self.settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
        raise PermissionDeniedException("Email verification required")

    # 3. Check if 2FA required
    if await self.requires_2fa(user):
        # Return partial token that only allows 2FA verification
        temp_token = await self.generate_temp_token(user)
        return LoginResponse(
            requires_2fa=True,
            temp_token=temp_token,
            message="Please provide your 2FA code"
        )

    # 4. Generate full access token
    access_token = await self.generate_access_token(user)
    return LoginResponse(
        access_token=access_token,
        requires_2fa=False
    )
```

## Security Considerations

1. **Rate Limiting**
   - Limit TOTP verification attempts
   - Implement exponential backoff
   - Track failed attempts per IP

2. **Backup Codes**
   - Generate cryptographically secure codes
   - Encrypt at rest
   - Single-use only
   - Allow regeneration with password confirmation

3. **Device Trust**
   - Optional "remember this device" feature
   - Secure device fingerprinting
   - Revocable device sessions

4. **Session Security**
   - Require fresh authentication for sensitive operations
   - Separate 2FA verification tokens from access tokens
   - Short-lived temporary tokens

## Testing Strategy

1. **Unit Tests**
   - TOTP generation and validation
   - Backup code generation and usage
   - Rate limiting logic

2. **Integration Tests**
   - Full authentication flow with 2FA
   - Setup and disable flows
   - Error scenarios

3. **Security Tests**
   - Brute force protection
   - Token security
   - Time drift tolerance

## Dependencies

```toml
# Add to pyproject.toml
[tool.poetry.dependencies]
pyotp = "^2.9.0"      # TOTP implementation
qrcode = "^7.4.2"     # QR code generation
pillow = "^10.0.0"    # Image processing for QR codes
```

## Migration Strategy

1. **Gradual Rollout**
   - Start with 2FA optional for all users
   - Enable requirement for admin users
   - Provide grace period for setup

2. **User Communication**
   - Email notifications about 2FA availability
   - In-app prompts for setup
   - Clear documentation

## Future Enhancements

1. **Additional 2FA Methods**
   - SMS codes (less secure, but familiar)
   - WebAuthn/FIDO2 support
   - Push notifications

2. **Advanced Features**
   - Risk-based authentication
   - Geolocation checks
   - Anomaly detection
