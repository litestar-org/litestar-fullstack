# Email Verification System

**Priority: HIGH** | **Effort: Medium** | **Phase: 1**

## Overview

Implement complete email verification system to verify user email addresses during registration and allow email changes with verification.

## Backend Tasks

### 1. Database Schema Updates

- [ ] **Add email verification fields to User model**
  - Add `email_verified_at: datetime | None` field
  - Add `email_verification_required: bool` field (default True)
  - Create migration: `app database make-migrations -m "add_email_verification_fields"`

- [ ] **Create EmailVerificationToken model**

  ```python
  # File: src/py/app/db/models/email_verification_token.py
  class EmailVerificationToken(UUIDAuditBase):
      __tablename__ = "email_verification_tokens"
      
      token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
      user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
      expires_at: Mapped[datetime] = mapped_column(DateTime)
      used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
      
      # Relationships
      user: Mapped["User"] = relationship("User", back_populates="verification_tokens")
  ```

- [ ] **Update User model relationships**

  ```python
  # Add to User model
  verification_tokens: Mapped[list["EmailVerificationToken"]] = relationship(
      "EmailVerificationToken", 
      back_populates="user",
      cascade="all, delete-orphan"
  )
  ```

### 2. Schema Updates (msgspec.Struct DTOs)

- [ ] **Create verification schemas**

  ```python
  # File: src/py/app/schemas/verification.py
  @dataclass
  class EmailVerificationRequest(msgspec.Struct):
      email: str = msgspec.field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
  
  @dataclass
  class EmailVerificationResponse(msgspec.Struct):
      message: str
      email: str
      
  @dataclass
  class VerifyEmailRequest(msgspec.Struct):
      token: str = msgspec.field(min_length=32, max_length=255)
  ```

- [ ] **Update account schemas**

  ```python
  # Add to existing AccountRegister
  email_verification_required: bool = True
  
  # Update UserRead to include verification status
  email_verified_at: datetime | None
  is_email_verified: bool  # computed property
  ```

### 3. Service Layer Implementation

- [ ] **Create EmailVerificationService**

  ```python
  # File: src/py/app/services/_email_verification.py
  class EmailVerificationService(service.SQLAlchemyAsyncRepositoryService[m.EmailVerificationToken]):
      class Repo(repository.SQLAlchemyAsyncRepository[m.EmailVerificationToken]):
          model_type = m.EmailVerificationToken
      repository_type = Repo
      
      async def create_verification_token(self, user_id: UUID) -> m.EmailVerificationToken
      async def verify_token(self, token: str) -> m.User | None
      async def cleanup_expired_tokens(self) -> int
      async def resend_verification(self, user_id: UUID) -> m.EmailVerificationToken
  ```

- [ ] **Update UserService with verification methods**

  ```python
  # Add to UserService
  async def mark_email_verified(self, user_id: UUID) -> m.User
  async def require_email_verification(self, user_id: UUID) -> bool
  async def is_email_verified(self, user_id: UUID) -> bool
  ```

### 4. Controller Implementation

- [ ] **Add verification endpoints to AccessController**

  ```python
  # Add to src/py/app/server/routes/access.py
  
  @post("/send-verification")
  async def send_verification_email(
      self, 
      data: EmailVerificationRequest,
      email_service: EmailService,
      verification_service: EmailVerificationService
  ) -> EmailVerificationResponse:
      """Send email verification to user"""
  
  @get("/verify-email")
  async def verify_email_token(
      self, 
      token: str = Parameter(query="token"),
      verification_service: EmailVerificationService
  ) -> UserRead:
      """Verify email with token"""
  
  @post("/resend-verification")
  async def resend_verification_email(
      self,
      current_user: User,
      email_service: EmailService,
      verification_service: EmailVerificationService
  ) -> EmailVerificationResponse:
      """Resend verification email to current user"""
  ```

### 5. Email Service Integration

- [ ] **Create email verification templates**

  ```html
  <!-- File: src/py/app/server/templates/emails/verify-email.html -->
  <!DOCTYPE html>
  <html>
  <head>
      <title>Verify Your Email Address</title>
  </head>
  <body>
      <h1>Welcome to {{ app_name }}!</h1>
      <p>Please verify your email address by clicking the link below:</p>
      <a href="{{ verification_url }}">Verify Email Address</a>
      <p>This link will expire in 24 hours.</p>
      <p>If you didn't create an account, you can safely ignore this email.</p>
  </body>
  </html>
  ```

- [ ] **Add verification email methods to EmailService**

  ```python
  # Add to EmailService
  async def send_verification_email(
      self, 
      user: User, 
      verification_token: str
  ) -> bool
  
  async def send_verification_success_email(
      self, 
      user: User
  ) -> bool
  ```

### 6. Security & Validation

- [ ] **Add email verification guard**

  ```python
  # File: src/py/app/server/guards.py
  def requires_verified_email(connection: ASGIConnection, _: Any) -> None:
      """Guard that requires user to have verified email."""
      if not connection.user.email_verified_at:
          raise PermissionDeniedException("Email verification required")
  ```

- [ ] **Add verification requirement to sensitive operations**
  - Team creation
  - Inviting team members
  - Changing critical settings

### 7. Background Jobs

- [ ] **Create cleanup job for expired tokens**

  ```python
  # File: src/py/app/server/jobs/email_verification.py
  from saq import Job
  
  async def cleanup_expired_verification_tokens(ctx: dict) -> None:
      """Remove expired email verification tokens"""
  ```

## Frontend Tasks

### 1. Email Verification Banner Component

- [ ] **Create EmailVerificationBanner component**

  ```tsx
  // File: src/js/src/components/auth/email-verification-banner.tsx
  interface EmailVerificationBannerProps {
    user: User;
    onResend: () => Promise<void>;
  }
  
  export function EmailVerificationBanner({ user, onResend }: EmailVerificationBannerProps) {
    // Show banner if email not verified
    // Include resend button with loading state
    // Handle success/error states
  }
  ```

### 2. Email Verification Page

- [ ] **Create email verification success page**

  ```tsx
  // File: src/js/src/routes/_public/verify-email.tsx
  export function VerifyEmailPage() {
    // Handle verification token from URL params
    // Show loading state while verifying
    // Show success/error results
    // Redirect to dashboard on success
  }
  ```

### 3. Update Signup Flow

- [ ] **Modify signup form to show verification notice**

  ```tsx
  // Update: src/js/src/components/auth/signup.tsx
  // After successful signup:
  // - Show success message with verification instructions
  // - Don't automatically redirect to dashboard
  // - Show "check your email" message
  ```

### 4. Update Auth Flow Integration

- [ ] **Add verification status to user context**

  ```tsx
  // Update: src/js/src/hooks/use-auth.ts
  // Include email verification status in user object
  // Add helper functions for checking verification
  ```

- [ ] **Update app layout to show verification banner**

  ```tsx
  // Update: src/js/src/layouts/app-layout.tsx
  // Show EmailVerificationBanner if user email not verified
  // Position at top of layout
  ```

### 5. Profile Settings Integration

- [ ] **Add email change with verification**

  ```tsx
  // Update profile settings to:
  // - Show current email verification status
  // - Allow email changes that trigger new verification
  // - Show pending email change status
  ```

## API Integration

### 1. Update Generated API Client

- [ ] **Run type generation after backend changes**

  ```bash
  make types
  ```

### 2. Add React Query Hooks

- [ ] **Create verification API hooks**

  ```tsx
  // File: src/js/src/lib/api/verification.ts
  export const useVerifyEmail = () => useMutation(...)
  export const useResendVerification = () => useMutation(...)
  export const useSendVerification = () => useMutation(...)
  ```

## Testing

### 1. Backend Tests

- [ ] **Test EmailVerificationService**
  - Token creation and validation
  - Token expiration handling
  - Cleanup functionality
  - Resend logic with rate limiting

- [ ] **Test verification endpoints**
  - Send verification email
  - Verify token (valid/invalid/expired)
  - Resend verification

- [ ] **Test verification guards**
  - Access blocked when email not verified
  - Access allowed when verified

### 2. Frontend Tests

- [ ] **Test EmailVerificationBanner component**
  - Shows when email not verified
  - Hides when email verified
  - Resend functionality

- [ ] **Test verification page**
  - Token verification flow
  - Success/error states
  - Redirect behavior

## Configuration

### 1. Settings Updates

- [ ] **Add verification settings**

  ```python
  # Add to settings
  EMAIL_VERIFICATION_REQUIRED: bool = True
  EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
  EMAIL_VERIFICATION_RATE_LIMIT: int = 3  # per hour
  ```

### 2. Environment Variables

- [ ] **Document required environment variables**

  ```bash
  # Email verification settings
  EMAIL_VERIFICATION_REQUIRED=true
  EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS=24
  ```

## Deployment Considerations

### 1. Migration Strategy

- [ ] **Plan migration for existing users**
  - Decide how to handle existing unverified users
  - Consider grace period for verification
  - Communication strategy

### 2. Feature Flag

- [ ] **Make verification optional initially**
  - Allow disabling verification for testing
  - Gradual rollout capability

## Success Criteria

- [ ] New users must verify email before accessing sensitive features
- [ ] Existing users can verify their email addresses
- [ ] Email changes require verification of new address
- [ ] Expired tokens are cleaned up automatically
- [ ] Rate limiting prevents verification spam
- [ ] Clear UX for verification status and actions
- [ ] 100% test coverage for verification flows
