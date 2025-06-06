# Configurable Authentication Settings

## Overview

Create a flexible authentication system where various security requirements can be configured through environment variables and settings.

## Authentication Configuration Matrix

### User Registration Settings

```python
@dataclass
class RegistrationSettings:
    # Registration requirements
    ALLOW_REGISTRATION: bool = True
    REQUIRE_EMAIL_VERIFICATION: bool = True
    EMAIL_VERIFICATION_TIMEOUT_HOURS: int = 24
    
    # Password policy
    MIN_PASSWORD_LENGTH: int = 12
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_DIGITS: bool = True
    REQUIRE_SPECIAL_CHARS: bool = True
    PASSWORD_HISTORY_COUNT: int = 5  # Prevent reuse of last N passwords
    
    # Username policy
    ALLOW_EMAIL_AS_USERNAME: bool = True
    MIN_USERNAME_LENGTH: int = 3
    MAX_USERNAME_LENGTH: int = 30
    USERNAME_REGEX: str = r"^[a-zA-Z0-9_-]+$"
```

### Login Security Settings

```python
@dataclass
class LoginSecuritySettings:
    # Basic login
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 30
    LOCKOUT_ESCALATION: bool = True  # Double lockout time on repeated failures
    
    # Session management
    SESSION_TIMEOUT_MINUTES: int = 60
    ABSOLUTE_TIMEOUT_HOURS: int = 24
    CONCURRENT_SESSIONS_ALLOWED: int = 3
    
    # Device tracking
    TRACK_DEVICES: bool = True
    DEVICE_TRUST_DAYS: int = 30
    REQUIRE_DEVICE_APPROVAL: bool = False
    
    # Geolocation
    CHECK_GEOLOCATION: bool = True
    ALERT_ON_NEW_LOCATION: bool = True
```

### 2FA Settings

```python
@dataclass
class TwoFactorSettings:
    # 2FA enforcement
    ENABLE_2FA: bool = True
    ENFORCE_2FA_FOR_ROLES: list[str] = field(default_factory=lambda: ["ADMIN", "SUPERUSER"])
    OPTIONAL_2FA_FOR_USERS: bool = True
    GRACE_PERIOD_DAYS: int = 7  # Days before 2FA becomes mandatory
    
    # TOTP configuration
    TOTP_ISSUER: str = "Litestar App"
    TOTP_ALGORITHM: str = "SHA1"  # SHA1, SHA256, SHA512
    TOTP_DIGITS: int = 6
    TOTP_INTERVAL: int = 30
    TOTP_VALID_WINDOW: int = 1  # Accept codes ±1 interval
    
    # Backup codes
    BACKUP_CODES_COUNT: int = 10
    BACKUP_CODE_LENGTH: int = 8
    WARN_LOW_BACKUP_CODES: int = 3
    
    # Recovery options
    ALLOW_SMS_RECOVERY: bool = False
    ALLOW_EMAIL_RECOVERY: bool = True
    RECOVERY_CODE_TIMEOUT_MINUTES: int = 15
```

### Advanced Security Settings

```python
@dataclass
class AdvancedSecuritySettings:
    # Suspicious activity detection
    ENABLE_ANOMALY_DETECTION: bool = True
    SUSPICIOUS_IP_THRESHOLD: int = 10  # Failed attempts from same IP
    SUSPICIOUS_USER_THRESHOLD: int = 5  # Failed attempts for same user
    
    # Re-authentication
    REQUIRE_FRESH_LOGIN_FOR: list[str] = field(
        default_factory=lambda: ["password_change", "2fa_disable", "email_change"]
    )
    FRESH_LOGIN_TIMEOUT_MINUTES: int = 15
    
    # Security headers
    ENABLE_CSRF_PROTECTION: bool = True
    ENABLE_CORS: bool = True
    CORS_ALLOWED_ORIGINS: list[str] = field(default_factory=lambda: ["http://localhost:3000"])
    
    # API security
    ENABLE_API_RATE_LIMITING: bool = True
    API_RATE_LIMIT_PER_MINUTE: int = 60
    API_RATE_LIMIT_PER_HOUR: int = 1000
```

## Implementation Approach

### 1. Settings Integration

```python
# app/lib/settings.py
@dataclass
class AuthenticationSettings:
    """Master authentication settings."""
    registration: RegistrationSettings = field(default_factory=RegistrationSettings)
    login_security: LoginSecuritySettings = field(default_factory=LoginSecuritySettings)
    two_factor: TwoFactorSettings = field(default_factory=TwoFactorSettings)
    advanced: AdvancedSecuritySettings = field(default_factory=AdvancedSecuritySettings)

# Load from environment
AUTH_REQUIRE_EMAIL_VERIFICATION=true
AUTH_ENABLE_2FA=true
AUTH_MAX_LOGIN_ATTEMPTS=5
```

### 2. Service Layer Integration

```python
class AuthenticationService:
    """Service handling all authentication logic."""
    
    def __init__(self, settings: AuthenticationSettings):
        self.settings = settings
    
    async def validate_registration(self, data: UserCreate) -> None:
        """Validate registration against current settings."""
        if not self.settings.registration.ALLOW_REGISTRATION:
            raise ClientException("Registration is currently disabled")
        
        # Validate password policy
        if len(data.password) < self.settings.registration.MIN_PASSWORD_LENGTH:
            raise ClientException(
                f"Password must be at least {self.settings.registration.MIN_PASSWORD_LENGTH} characters"
            )
        
        # Additional validations...
    
    async def check_login_requirements(self, user: User) -> LoginRequirements:
        """Check what's required for login."""
        requirements = LoginRequirements()
        
        # Email verification
        if self.settings.registration.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
            requirements.email_verification_required = True
        
        # 2FA check
        if self.settings.two_factor.ENABLE_2FA:
            if user.role in self.settings.two_factor.ENFORCE_2FA_FOR_ROLES:
                requirements.two_factor_required = True
            elif user.has_2fa_enabled:
                requirements.two_factor_required = True
        
        return requirements
```

### 3. Dynamic Guard System

```python
def create_conditional_guard(setting_path: str):
    """Create a guard that checks a setting dynamically."""
    def guard(connection: ASGIConnection, handler: BaseRouteHandler) -> None:
        settings = get_settings()
        if not getattr(settings.auth, setting_path):
            raise PermissionDeniedException(f"{setting_path} is required")
    return guard

# Usage
requires_verified_email = create_conditional_guard("registration.REQUIRE_EMAIL_VERIFICATION")
requires_2fa = create_conditional_guard("two_factor.ENABLE_2FA")
```

### 4. Frontend Integration

```typescript
// Types for authentication requirements
interface AuthSettings {
  registration: {
    allowRegistration: boolean;
    requireEmailVerification: boolean;
    passwordPolicy: PasswordPolicy;
  };
  twoFactor: {
    enabled: boolean;
    required: boolean;
    gracePeriodDays: number;
  };
  // ... other settings
}

// Get settings from API
const { data: authSettings } = useQuery({
  queryKey: ['auth-settings'],
  queryFn: () => api.auth.getSettings()
});

// Dynamic UI based on settings
function LoginForm() {
  const settings = useAuthSettings();
  
  return (
    <form>
      {/* Password input */}
      {settings?.twoFactor.enabled && (
        <TwoFactorInput />
      )}
    </form>
  );
}
```

## Configuration Examples

### Development Environment
```env
# Relaxed settings for development
AUTH_REQUIRE_EMAIL_VERIFICATION=false
AUTH_ENABLE_2FA=false
AUTH_MAX_LOGIN_ATTEMPTS=999
AUTH_MIN_PASSWORD_LENGTH=8
```

### Staging Environment
```env
# Moderate security for testing
AUTH_REQUIRE_EMAIL_VERIFICATION=true
AUTH_ENABLE_2FA=true
AUTH_OPTIONAL_2FA_FOR_USERS=true
AUTH_MAX_LOGIN_ATTEMPTS=10
AUTH_MIN_PASSWORD_LENGTH=10
```

### Production Environment
```env
# Maximum security
AUTH_REQUIRE_EMAIL_VERIFICATION=true
AUTH_ENABLE_2FA=true
AUTH_ENFORCE_2FA_FOR_ROLES=["ADMIN","SUPERUSER","USER"]
AUTH_MAX_LOGIN_ATTEMPTS=3
AUTH_MIN_PASSWORD_LENGTH=16
AUTH_ENABLE_ANOMALY_DETECTION=true
AUTH_REQUIRE_DEVICE_APPROVAL=true
```

## Testing Strategy

1. **Configuration Tests**
   - Test each setting combination
   - Verify defaults work correctly
   - Test environment variable loading

2. **Integration Tests**
   - Test authentication flow with different settings
   - Verify guards respect settings
   - Test setting changes at runtime

3. **Security Tests**
   - Verify security features can't be bypassed
   - Test rate limiting and lockouts
   - Verify proper error messages

## Future Enhancements

1. **Admin UI for Settings**
   - Web interface to change settings
   - Audit log for setting changes
   - Setting validation

2. **Per-Organization Settings**
   - Different settings for different tenants
   - Hierarchical setting inheritance
   - Setting templates

3. **A/B Testing**
   - Test different security settings
   - Gradual rollout of changes
   - User feedback collection