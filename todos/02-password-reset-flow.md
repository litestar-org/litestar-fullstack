# Password Reset Flow

**Priority: HIGH** | **Effort: Medium** | **Phase: 1**

## Overview
Implement secure password reset functionality allowing users to reset forgotten passwords via email tokens. Addresses GitHub issue requirements and follows security best practices.

## Backend Tasks

### 1. Database Schema Updates
- [ ] **Create PasswordResetToken model**
  ```python
  # File: src/py/app/db/models/password_reset_token.py
  class PasswordResetToken(UUIDAuditBase):
      __tablename__ = "password_reset_tokens"
      
      token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
      user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
      expires_at: Mapped[datetime] = mapped_column(DateTime)
      used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
      ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv6 support
      user_agent: Mapped[str | None] = mapped_column(Text)
      
      # Relationships
      user: Mapped["User"] = relationship("User", back_populates="reset_tokens")
  ```

- [ ] **Update User model relationships**
  ```python
  # Add to User model
  reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
      "PasswordResetToken", 
      back_populates="user",
      cascade="all, delete-orphan"
  )
  
  # Add security tracking fields
  password_reset_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
  failed_reset_attempts: Mapped[int] = mapped_column(Integer, default=0)
  reset_locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
  ```

### 2. Enhanced Password Validation (Addresses GitHub Issue #180)
- [ ] **Create production-ready password validation**
  ```python
  # File: src/py/app/lib/validation.py
  import re
  from typing import Annotated
  import msgspec
  
  class PasswordStr(str):
      """Production-ready password validation"""
      @classmethod
      def __get_validators__(cls):
          yield cls.validate
      
      @classmethod
      def validate(cls, v: str) -> str:
          if len(v) < 12:
              raise ValueError("Password must be at least 12 characters")
          if len(v) > 128:
              raise ValueError("Password must not exceed 128 characters")
          if not re.search(r'[A-Z]', v):
              raise ValueError("Password must contain uppercase letter")
          if not re.search(r'[a-z]', v):
              raise ValueError("Password must contain lowercase letter")
          if not re.search(r'\d', v):
              raise ValueError("Password must contain digit")
          if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
              raise ValueError("Password must contain special character")
          
          # Check against common passwords
          if v.lower() in COMMON_PASSWORDS:
              raise ValueError("Password is too common")
          
          return v
  
  # Password type annotation
  Password = Annotated[PasswordStr, msgspec.Meta(min_length=12, max_length=128)]
  ```

### 3. Schema Updates (msgspec.Struct DTOs)
- [ ] **Create password reset schemas**
  ```python
  # File: src/py/app/schemas/password_reset.py
  from app.lib.validation import Password
  
  @dataclass
  class ForgotPasswordRequest(msgspec.Struct):
      email: str = msgspec.field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
  
  @dataclass
  class ForgotPasswordResponse(msgspec.Struct):
      message: str
      email: str
      expires_in_minutes: int
  
  @dataclass
  class ResetPasswordRequest(msgspec.Struct):
      token: str = msgspec.field(min_length=32, max_length=255)
      password: Password
      password_confirm: Password
      
      def __post_init__(self):
          if self.password != self.password_confirm:
              raise ValueError("Passwords do not match")
  
  @dataclass
  class ValidateResetTokenRequest(msgspec.Struct):
      token: str = msgspec.field(min_length=32, max_length=255)
  
  @dataclass
  class ResetPasswordResponse(msgspec.Struct):
      message: str
      user_id: str
  ```

### 4. Service Layer Implementation
- [ ] **Create PasswordResetService**
  ```python
  # File: src/py/app/services/_password_reset.py
  import secrets
  from datetime import datetime, timedelta
  
  class PasswordResetService(service.SQLAlchemyAsyncRepositoryService[m.PasswordResetToken]):
      class Repo(repository.SQLAlchemyAsyncRepository[m.PasswordResetToken]):
          model_type = m.PasswordResetToken
      repository_type = Repo
      
      async def create_reset_token(
          self, 
          user_id: UUID, 
          ip_address: str, 
          user_agent: str
      ) -> m.PasswordResetToken:
          """Create secure reset token with tracking"""
          
      async def validate_reset_token(self, token: str) -> m.User | None:
          """Validate token and return user if valid"""
          
      async def use_reset_token(self, token: str, new_password: str) -> m.User:
          """Use token to reset password and mark as used"""
          
      async def cleanup_expired_tokens(self) -> int:
          """Remove expired tokens"""
          
      async def check_rate_limit(self, email: str, ip_address: str) -> bool:
          """Check if user/IP has exceeded reset attempt limits"""
          
      async def increment_failed_attempt(self, user_id: UUID) -> None:
          """Track failed reset attempts"""
  ```

- [ ] **Update UserService with password reset methods**
  ```python
  # Add to UserService
  async def request_password_reset(
      self, 
      email: str, 
      ip_address: str, 
      user_agent: str
  ) -> bool:
      """Request password reset for email"""
      
  async def reset_password_with_token(
      self, 
      token: str, 
      new_password: str
  ) -> m.User:
      """Reset password using valid token"""
      
  async def is_reset_rate_limited(self, user_id: UUID) -> bool:
      """Check if user is rate limited for resets"""
  ```

### 5. Controller Implementation
- [ ] **Add password reset endpoints to AccessController**
  ```python
  # Add to src/py/app/server/routes/access.py
  
  @post("/forgot-password")
  async def forgot_password(
      self,
      data: ForgotPasswordRequest,
      request: Request,
      user_service: UserService,
      password_reset_service: PasswordResetService,
      email_service: EmailService
  ) -> ForgotPasswordResponse:
      """Initiate password reset flow"""
      # Rate limiting by IP and email
      # Send reset email if user exists (or fake success for security)
      
  @get("/reset-password")
  async def validate_reset_token(
      self,
      token: str = Parameter(query="token"),
      password_reset_service: PasswordResetService
  ) -> dict:
      """Validate reset token before showing reset form"""
      
  @post("/reset-password")
  async def reset_password_with_token(
      self,
      data: ResetPasswordRequest,
      request: Request,
      password_reset_service: PasswordResetService,
      email_service: EmailService
  ) -> ResetPasswordResponse:
      """Complete password reset with token"""
      # Log security event
      # Send confirmation email
      # Invalidate all existing sessions
  ```

### 6. Email Templates (Addresses GitHub Issue #51)
- [ ] **Create password reset email template**
  ```html
  <!-- File: src/py/app/server/templates/emails/password-reset.html -->
  <!DOCTYPE html>
  <html>
  <head>
      <title>Reset Your Password</title>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
  </head>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
      <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h1 style="color: #2563eb;">Reset Your Password</h1>
          
          <p>Hello {{ user.name or user.email }},</p>
          
          <p>We received a request to reset your password for your {{ app_name }} account.</p>
          
          <div style="text-align: center; margin: 30px 0;">
              <a href="{{ reset_url }}" 
                 style="background-color: #2563eb; color: white; padding: 12px 24px; 
                        text-decoration: none; border-radius: 6px; display: inline-block;">
                  Reset Your Password
              </a>
          </div>
          
          <p>This link will expire in {{ expires_in_hours }} hours.</p>
          
          <p><strong>If you didn't request this reset:</strong></p>
          <ul>
              <li>You can safely ignore this email</li>
              <li>Your password will not be changed</li>
              <li>Consider changing your password if you suspect unauthorized access</li>
          </ul>
          
          <hr style="margin: 30px 0; border: 1px solid #eee;">
          
          <p style="font-size: 12px; color: #666;">
              This reset was requested from IP: {{ ip_address }}<br>
              If this wasn't you, please contact support immediately.
          </p>
      </div>
  </body>
  </html>
  ```

- [ ] **Create password reset confirmation template**
  ```html
  <!-- File: src/py/app/server/templates/emails/password-reset-confirmation.html -->
  <!DOCTYPE html>
  <html>
  <head>
      <title>Password Reset Successful</title>
  </head>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
      <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h1 style="color: #16a34a;">Password Reset Successful</h1>
          
          <p>Hello {{ user.name or user.email }},</p>
          
          <p>Your password has been successfully reset at {{ reset_time }}.</p>
          
          <p><strong>Security Information:</strong></p>
          <ul>
              <li>Reset from IP: {{ ip_address }}</li>
              <li>All existing sessions have been invalidated</li>
              <li>You'll need to log in again on all devices</li>
          </ul>
          
          <p>If you didn't make this change, please contact support immediately.</p>
          
          <div style="text-align: center; margin: 30px 0;">
              <a href="{{ login_url }}" 
                 style="background-color: #16a34a; color: white; padding: 12px 24px; 
                        text-decoration: none; border-radius: 6px; display: inline-block;">
                  Log In Now
              </a>
          </div>
      </div>
  </body>
  </html>
  ```

### 7. Security Features
- [ ] **Add rate limiting middleware**
  ```python
  # File: src/py/app/lib/rate_limiting.py
  from litestar.middleware.rate_limit import RateLimitConfig
  
  PASSWORD_RESET_RATE_LIMIT = RateLimitConfig(
      rate_limit=("minute", 3),  # 3 attempts per minute
      exclude_opt_key="no_rate_limit"
  )
  ```

- [ ] **Add security logging**
  ```python
  # File: src/py/app/lib/security_logger.py
  async def log_password_reset_attempt(
      email: str,
      ip_address: str,
      user_agent: str,
      success: bool
  ) -> None:
      """Log password reset attempts for security monitoring"""
  ```

### 8. Background Jobs
- [ ] **Create cleanup jobs**
  ```python
  # File: src/py/app/server/jobs/password_reset.py
  
  async def cleanup_expired_reset_tokens(ctx: dict) -> None:
      """Remove expired password reset tokens"""
      
  async def cleanup_rate_limit_data(ctx: dict) -> None:
      """Clean up old rate limiting data"""
  ```

## Frontend Tasks

### 1. Forgot Password Form
- [ ] **Create ForgotPasswordForm component**
  ```tsx
  // File: src/js/src/components/auth/forgot-password-form.tsx
  interface ForgotPasswordFormProps {
    onSuccess: (email: string) => void;
    onError: (error: string) => void;
  }
  
  export function ForgotPasswordForm({ onSuccess, onError }: ForgotPasswordFormProps) {
    // Email input with validation
    // Submit handling with loading state
    // Success message display
    // Error handling and display
  }
  ```

### 2. Reset Password Form with Validation
- [ ] **Create ResetPasswordForm component**
  ```tsx
  // File: src/js/src/components/auth/reset-password-form.tsx
  interface ResetPasswordFormProps {
    token: string;
    onSuccess: () => void;
    onError: (error: string) => void;
  }
  
  export function ResetPasswordForm({ token, onSuccess, onError }: ResetPasswordFormProps) {
    // Password input with strength indicator
    // Confirm password validation
    // Real-time validation feedback
    // Submit handling
  }
  ```

### 3. Password Strength Indicator
- [ ] **Create PasswordStrengthIndicator component**
  ```tsx
  // File: src/js/src/components/ui/password-strength-indicator.tsx
  interface PasswordStrengthIndicatorProps {
    password: string;
    requirements?: PasswordRequirement[];
  }
  
  export function PasswordStrengthIndicator({ password, requirements }: PasswordStrengthIndicatorProps) {
    // Visual strength meter
    // Requirements checklist
    // Color-coded feedback
    // Accessibility support
  }
  ```

### 4. Route Pages
- [ ] **Create forgot password page**
  ```tsx
  // File: src/js/src/routes/_public/forgot-password.tsx
  export function ForgotPasswordPage() {
    // ForgotPasswordForm integration
    // Success state handling
    // Navigation logic
  }
  ```

- [ ] **Create reset password page**
  ```tsx
  // File: src/js/src/routes/_public/reset-password.tsx
  export function ResetPasswordPage() {
    // Token validation on load
    // ResetPasswordForm integration
    // Success/error state handling
    // Redirect after success
  }
  ```

### 5. Update Login Form
- [ ] **Add forgot password link to login form**
  ```tsx
  // Update: src/js/src/components/auth/login.tsx
  // Add "Forgot your password?" link
  // Style consistently with design system
  ```

### 6. Password Requirements Display
- [ ] **Create PasswordRequirements component**
  ```tsx
  // File: src/js/src/components/auth/password-requirements.tsx
  export function PasswordRequirements() {
    // Display password policy requirements
    // Used in signup and reset forms
    // Clear, user-friendly language
  }
  ```

## API Integration

### 1. Update Generated API Client
- [ ] **Run type generation after backend changes**
  ```bash
  make types
  ```

### 2. Add React Query Hooks
- [ ] **Create password reset API hooks**
  ```tsx
  // File: src/js/src/lib/api/password-reset.ts
  export const useForgotPassword = () => useMutation(...)
  export const useResetPassword = () => useMutation(...)
  export const useValidateResetToken = () => useQuery(...)
  ```

### 3. Form Validation
- [ ] **Add client-side password validation**
  ```tsx
  // File: src/js/src/lib/validation/password.ts
  export interface PasswordRequirements {
    minLength: boolean;
    hasUppercase: boolean;
    hasLowercase: boolean;
    hasNumber: boolean;
    hasSpecialChar: boolean;
    isNotCommon: boolean;
  }
  
  export function validatePassword(password: string): PasswordRequirements
  export function getPasswordStrength(password: string): 'weak' | 'medium' | 'strong'
  ```

## Testing

### 1. Backend Tests
- [ ] **Test PasswordResetService**
  - Token generation and validation
  - Rate limiting functionality
  - Security logging
  - Token expiration handling
  - Failed attempt tracking

- [ ] **Test password reset endpoints**
  - Forgot password flow (valid/invalid emails)
  - Token validation
  - Password reset completion
  - Rate limiting enforcement
  - Security event logging

- [ ] **Test password validation**
  - Password strength requirements
  - Common password detection
  - Edge cases and error handling

### 2. Frontend Tests
- [ ] **Test ForgotPasswordForm**
  - Email validation
  - Submit functionality
  - Success/error states
  - Loading states

- [ ] **Test ResetPasswordForm**
  - Password validation
  - Confirm password matching
  - Strength indicator
  - Submit functionality

- [ ] **Test PasswordStrengthIndicator**
  - Strength calculation
  - Visual feedback
  - Requirements display

### 3. Integration Tests
- [ ] **Test complete password reset flow**
  - Request reset → receive email → reset password
  - Token expiration handling
  - Rate limiting across requests
  - Security logging verification

## Configuration

### 1. Settings Updates
- [ ] **Add password reset settings**
  ```python
  # Add to settings
  PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
  PASSWORD_RESET_RATE_LIMIT_PER_HOUR: int = 3
  PASSWORD_RESET_RATE_LIMIT_PER_IP: int = 10
  PASSWORD_MIN_LENGTH: int = 12
  PASSWORD_REQUIRE_UPPERCASE: bool = True
  PASSWORD_REQUIRE_LOWERCASE: bool = True
  PASSWORD_REQUIRE_NUMBERS: bool = True
  PASSWORD_REQUIRE_SPECIAL_CHARS: bool = True
  ```

### 2. Environment Variables
- [ ] **Document security settings**
  ```bash
  # Password reset settings
  PASSWORD_RESET_TOKEN_EXPIRE_HOURS=1
  PASSWORD_RESET_RATE_LIMIT_PER_HOUR=3
  PASSWORD_MIN_LENGTH=12
  ```

## Security Considerations

### 1. Rate Limiting
- [ ] **Implement comprehensive rate limiting**
  - Per email address (3 attempts/hour)
  - Per IP address (10 attempts/hour)
  - Global rate limiting for extreme cases

### 2. Token Security
- [ ] **Ensure secure token generation**
  - Cryptographically secure random tokens
  - Sufficient entropy (256 bits minimum)
  - One-time use tokens
  - Short expiration times (1 hour)

### 3. Information Disclosure Prevention
- [ ] **Prevent user enumeration**
  - Same response for valid/invalid emails
  - Consistent timing for all requests
  - No indication if email exists

### 4. Audit Logging
- [ ] **Log all security events**
  - Reset requests (successful and failed)
  - Token usage
  - Rate limit violations
  - Suspicious patterns

## Success Criteria
- [ ] Users can securely reset forgotten passwords
- [ ] Strong password requirements enforced
- [ ] Rate limiting prevents abuse
- [ ] No user enumeration possible
- [ ] All security events logged
- [ ] Email templates are professional and clear
- [ ] Mobile-responsive UI
- [ ] 100% test coverage for security-critical flows
- [ ] Meets production security standards