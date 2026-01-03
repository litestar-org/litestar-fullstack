# PRD: Litestar Fullstack SPA - Inertia Feature Parity

## Document Information

| Field | Value |
|-------|-------|
| **Feature Name** | Inertia to SPA Feature Parity |
| **Slug** | `inertia-spa-parity` |
| **Complexity** | Complex (10+ phases) |
| **Created** | 2025-12-29 |
| **Status** | Ready for Implementation |

---

## 1. Intelligence Context

### 1.1 Complexity Assessment

This is a **COMPLEX** implementation requiring 10+ phases. The analysis involved:

- Comprehensive codebase comparison between `litestar-fullstack-inertia` and `litestar-fullstack-spa`
- Multi-model AI consensus (Gemini 3 Pro + GPT 5.2) on authentication architecture
- Detailed gap analysis across backend, frontend, and deployment tooling

### 1.2 Similar Features Referenced

Pattern analysis drew from existing implementations:

- `src/py/app/domain/accounts/services/_user.py` - Service pattern with inner repository
- `src/py/app/domain/accounts/controllers/_access.py` - Controller patterns for auth
- `src/py/app/domain/accounts/controllers/_oauth.py` - OAuth flow patterns
- `src/py/app/lib/crypt.py` - Existing TOTP/cryptographic functions
- `src/py/app/domain/teams/` - Domain structure pattern

### 1.3 Patterns to Follow

All implementations must follow:

- **Service Pattern**: Inner `Repo` class within `SQLAlchemyAsyncRepositoryService`
- **Schema Pattern**: `CamelizedBaseStruct` from msgspec (never dicts or Pydantic)
- **Model Pattern**: `UUIDAuditBase` with `Mapped[]` typing
- **Controller Pattern**: Litestar `Controller` with dependency injection via `Provide`
- **Frontend Pattern**: TanStack Router file-based routes with TanStack Query hooks

---

## 2. Problem Statement

### 2.1 User Problem Being Solved

The `litestar-fullstack-spa` project needs complete feature parity with the `litestar-fullstack-inertia` reference implementation. Users of the SPA template expect:

1. **Production-ready deployment** - One-command Railway deployment with environment configuration
2. **Secure authentication** - JWT with refresh tokens, MFA/TOTP support, proper token rotation
3. **OAuth account management** - Link/unlink providers from profile, not just login
4. **Administrative capabilities** - User management, team oversight, audit logging
5. **Modern security standards** - CSRF protection, refresh token rotation with reuse detection

### 2.2 Business Value

- **Template completeness** - SPA template matches Inertia template capabilities
- **Production readiness** - Railway deployment enables quick production launches
- **Security compliance** - Modern auth patterns meet enterprise requirements
- **Developer experience** - Complete feature set reduces custom development

### 2.3 Success Criteria

All of the following must be achieved:

- [ ] Railway deployment works with single `./deploy.sh` command
- [ ] MFA can be enabled, configured, and used during login
- [ ] OAuth accounts can be linked/unlinked from user profile
- [ ] Admin dashboard displays user/team statistics
- [ ] Admin can manage users and view audit logs
- [ ] Refresh tokens rotate properly with reuse detection
- [ ] CSRF protection active on all mutation endpoints
- [ ] All existing tests continue to pass
- [ ] New features have 90%+ test coverage

---

## 3. Acceptance Criteria

### 3.1 Railway Deployment

**REQUIRED:**

- [ ] `tools/deploy/railway/deploy.sh` creates new Railway project
- [ ] Script provisions PostgreSQL database automatically
- [ ] Script configures all required environment variables
- [ ] Script generates public domain
- [ ] Health check passes after deployment
- [ ] `tools/deploy/railway/env-setup.sh` configures Resend email
- [ ] `env-setup.sh` configures GitHub OAuth credentials
- [ ] `env-setup.sh` configures Google OAuth credentials
- [ ] `railway.json` specifies Dockerfile.distroless builder
- [ ] Pre-deploy runs database migrations automatically

### 3.2 Authentication & Refresh Tokens

**REQUIRED:**

- [ ] Login returns access token (15 min) + refresh token (7 days) in HTTP-only cookies
- [ ] Access token cookie: `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`
- [ ] Refresh token cookie: `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/api/auth/refresh`
- [ ] `POST /api/auth/refresh` rotates refresh token
- [ ] Refresh tokens stored as SHA-256 hashes in database
- [ ] Each refresh token has `family_id` for reuse detection
- [ ] Reused refresh token triggers family-wide revocation
- [ ] Background job cleans up expired refresh tokens
- [ ] CSRF token required for all non-GET requests
- [ ] CSRF token provided in non-HttpOnly cookie

### 3.3 MFA/TOTP System

**REQUIRED:**

- [ ] `POST /api/mfa/enable` returns TOTP secret + QR code (base64 PNG)
- [ ] `POST /api/mfa/confirm` verifies 6-digit code and enables MFA
- [ ] Confirmation returns 8 backup codes (shown once, stored hashed)
- [ ] `DELETE /api/mfa/disable` requires password confirmation
- [ ] `POST /api/mfa/regenerate-codes` generates new backup codes
- [ ] Login with MFA returns challenge token (not full auth)
- [ ] `POST /api/mfa/challenge/verify` accepts TOTP or backup code
- [ ] Challenge token has `type: "mfa_challenge"`, `aud: "mfa_verification"`
- [ ] Challenge token expires in 5 minutes
- [ ] Successful MFA verification issues full auth tokens
- [ ] Backup code usage decrements remaining count
- [ ] Warning shown when 2 or fewer backup codes remain

### 3.4 OAuth Account Management

**REQUIRED:**

- [ ] `GET /api/profile/oauth/accounts` lists linked providers
- [ ] `POST /api/profile/oauth/{provider}/link` initiates linking flow
- [ ] `GET /api/profile/oauth/{provider}/complete` completes linking
- [ ] `DELETE /api/profile/oauth/{provider}` unlinks account
- [ ] Cannot unlink if only auth method and no password set
- [ ] `POST /api/profile/oauth/{provider}/upgrade-scopes` re-authorizes with more permissions
- [ ] OAuth provider tokens stored encrypted in database
- [ ] Background job refreshes expiring OAuth tokens (where supported)

### 3.5 Admin Domain

**REQUIRED:**

- [ ] `GET /api/admin/dashboard` returns user/team statistics
- [ ] Statistics include: total users, active users, verified users, total teams, recent signups
- [ ] `GET /api/admin/users` lists users with pagination
- [ ] `GET /api/admin/users/{id}` returns user details
- [ ] `PATCH /api/admin/users/{id}` updates user (roles, active status)
- [ ] `GET /api/admin/teams` lists teams with pagination
- [ ] `GET /api/admin/teams/{id}` returns team details with members
- [ ] `GET /api/admin/audit` returns audit log with filtering
- [ ] All admin endpoints require `is_superuser` guard
- [ ] Audit log records: actor, action, target, details, IP, timestamp

### 3.6 Frontend Pages

**REQUIRED:**

- [ ] `/mfa-challenge` page for MFA verification during login
- [ ] Profile page has MFA settings section
- [ ] MFA setup shows QR code in dialog
- [ ] Backup codes displayed in modal (copy functionality)
- [ ] Profile page has Connected Accounts section
- [ ] Connected accounts show link/unlink buttons per provider
- [ ] `/admin` dashboard with statistics cards
- [ ] `/admin/users` with DataTable (search, pagination)
- [ ] `/admin/users/:id` user detail page
- [ ] `/admin/teams` with DataTable
- [ ] `/admin/teams/:id` team detail page
- [ ] `/admin/audit` with filterable audit log table
- [ ] Admin nav link visible only to superusers
- [ ] Silent token refresh on 401 responses

### 3.7 Database Changes

**REQUIRED:**

- [ ] `refresh_token` table created with migration
- [ ] `audit_log` table created with migration
- [ ] User model has `totp_secret` (EncryptedString)
- [ ] User model has `is_two_factor_enabled` (bool, default false)
- [ ] User model has `two_factor_confirmed_at` (datetime, nullable)
- [ ] User model has `backup_codes` (JSONB, nullable)
- [ ] Indexes on `refresh_token.user_id`, `refresh_token.family_id`
- [ ] Indexes on `audit_log.actor_id`, `audit_log.action`, `audit_log.created_at`

---

## 4. Technical Approach

### 4.1 File Structure Plan

#### New Backend Files (Required)

```
src/py/app/
├── db/models/
│   ├── refresh_token.py          # NEW: Refresh token storage
│   └── audit_log.py              # NEW: Audit log model
├── domain/
│   ├── accounts/controllers/
│   │   ├── _mfa.py               # NEW: MFA management
│   │   └── _mfa_challenge.py     # NEW: MFA during login
│   └── admin/                    # NEW: Entire domain
│       ├── __init__.py
│       ├── deps.py
│       ├── schemas/
│       ├── controllers/
│       │   ├── __init__.py
│       │   ├── _dashboard.py
│       │   ├── _users.py
│       │   ├── _teams.py
│       │   └── _audit.py
│       └── services/
│           ├── __init__.py
│           └── _audit.py
└── server/
    └── plugins.py                # MODIFY: Register admin routes

tools/deploy/railway/
├── deploy.sh                     # NEW: Railway deployment
├── env-setup.sh                  # NEW: Environment config
└── .env.railway.example          # NEW: Example env file

railway.json                      # NEW: Railway config
```

#### New Frontend Files (Required)

```
src/js/src/
├── components/
│   ├── auth/
│   │   ├── mfa-setup-dialog.tsx      # NEW
│   │   ├── mfa-disable-dialog.tsx    # NEW
│   │   ├── backup-codes-display.tsx  # NEW
│   │   └── totp-input.tsx            # NEW
│   ├── profile/
│   │   ├── mfa-section.tsx           # NEW
│   │   └── connected-accounts.tsx    # NEW
│   └── admin/
│       ├── stats-cards.tsx           # NEW
│       ├── recent-activity.tsx       # NEW
│       ├── user-table.tsx            # NEW
│       ├── team-table.tsx            # NEW
│       └── audit-log-table.tsx       # NEW
├── hooks/
│   ├── use-mfa.ts                    # NEW
│   └── use-admin.ts                  # NEW
└── routes/
    ├── _public/
    │   └── mfa-challenge.tsx         # NEW
    └── _app/
        └── admin/
            ├── index.tsx             # NEW: Dashboard
            ├── users/
            │   ├── index.tsx         # NEW: User list
            │   └── $userId.tsx       # NEW: User detail
            ├── teams/
            │   ├── index.tsx         # NEW: Team list
            │   └── $teamId.tsx       # NEW: Team detail
            └── audit.tsx             # NEW: Audit log
```

### 4.2 Database Schema Changes

#### RefreshToken Model
```python
class RefreshToken(UUIDAuditBase):
    """Refresh token storage for JWT rotation."""

    __tablename__ = "refresh_token"
    __table_args__ = {"comment": "JWT refresh tokens with rotation tracking"}

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 hex
        unique=True,
        index=True
    )
    family_id: Mapped[UUID] = mapped_column(index=True)
    expires_at: Mapped[datetime] = mapped_column()
    revoked_at: Mapped[datetime | None] = mapped_column(default=None)
    device_info: Mapped[str | None] = mapped_column(String(255), default=None)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
```

#### AuditLog Model
```python
class AuditLog(UUIDAuditBase):
    """Audit log for administrative actions."""

    __tablename__ = "audit_log"
    __table_args__ = {"comment": "Administrative audit trail"}

    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        index=True
    )
    actor_email: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[UUID | None] = mapped_column()
    target_label: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[dict | None] = mapped_column(JSONB, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45))

    # Relationships
    actor: Mapped["User | None"] = relationship()
```

#### User Model Additions
```python
# Add to existing User model
totp_secret: Mapped[str | None] = mapped_column(
    EncryptedString(),
    deferred_group="security_sensitive",
    default=None
)
is_two_factor_enabled: Mapped[bool] = mapped_column(default=False)
two_factor_confirmed_at: Mapped[datetime | None] = mapped_column(default=None)
backup_codes: Mapped[list | None] = mapped_column(JSONB, default=None)

# Relationship
refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan"
)
```

### 4.3 API Endpoints Summary

#### Authentication Extensions
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/refresh` | Rotate refresh token |
| POST | `/api/mfa/enable` | Generate TOTP secret |
| POST | `/api/mfa/confirm` | Confirm MFA setup |
| DELETE | `/api/mfa/disable` | Disable MFA |
| POST | `/api/mfa/regenerate-codes` | New backup codes |
| POST | `/api/mfa/challenge/verify` | Verify during login |

#### Profile OAuth Extensions
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/profile/oauth/accounts` | List linked accounts |
| POST | `/api/profile/oauth/{provider}/link` | Start linking |
| GET | `/api/profile/oauth/{provider}/complete` | Complete linking |
| DELETE | `/api/profile/oauth/{provider}` | Unlink account |

#### Admin Domain
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/dashboard` | Statistics |
| GET | `/api/admin/users` | User list |
| GET | `/api/admin/users/{id}` | User detail |
| PATCH | `/api/admin/users/{id}` | Update user |
| GET | `/api/admin/teams` | Team list |
| GET | `/api/admin/teams/{id}` | Team detail |
| GET | `/api/admin/audit` | Audit log |

### 4.4 Security Implementation

#### CSRF Configuration
```python
from litestar.middleware.csrf import CSRFConfig

csrf_config = CSRFConfig(
    secret=settings.SECRET_KEY,
    cookie_name="csrf_token",
    cookie_secure=True,
    cookie_httponly=False,  # Frontend needs to read it
    cookie_samesite="lax",
    header_name="X-CSRF-Token",
    safe_methods={"GET", "HEAD", "OPTIONS", "TRACE"}
)
```

#### Cookie Configuration
```python
# Access token cookie
access_cookie = Cookie(
    key="access_token",
    httponly=True,
    secure=True,
    samesite="lax",
    path="/",
    max_age=900  # 15 minutes
)

# Refresh token cookie
refresh_cookie = Cookie(
    key="refresh_token",
    httponly=True,
    secure=True,
    samesite="strict",
    path="/api/auth/refresh",
    max_age=604800  # 7 days
)
```

---

## 5. Testing Strategy

### 5.1 Unit Tests (Required - 90%+ coverage)

**Authentication tests:**

- `test_refresh_token_rotation.py`
  - Token rotation issues new pair
  - Reuse detection triggers family revocation
  - Expired tokens rejected
  - Invalid tokens rejected

- `test_mfa_service.py`
  - TOTP secret generation
  - TOTP code verification
  - Backup code generation and hashing
  - Backup code verification and decrement

**Admin tests:**

- `test_audit_service.py`
  - Audit log creation
  - Filtering and pagination
  - Actor/target relationships

### 5.2 Integration Tests (Required)

**Auth flow tests:**

- `test_mfa_flow.py`
  - Enable MFA end-to-end
  - Login with MFA challenge
  - Backup code usage
  - Disable MFA

- `test_refresh_flow.py`
  - Full refresh rotation cycle
  - Concurrent refresh handling
  - Reuse detection scenario

**Admin tests:**

- `test_admin_endpoints.py`
  - Dashboard statistics accuracy
  - User management operations
  - Audit log recording

### 5.3 Frontend Tests (Required)

- MFA setup dialog renders QR code
- Backup codes display with copy functionality
- Admin tables handle pagination
- Silent refresh interceptor works

---

## 6. Implementation Notes

### 6.1 Pattern Deviations

**None** - All implementations must follow established patterns exactly.

### 6.2 Dependencies

**Backend (already in pyproject.toml):**

- `pyotp>=2.9.0` - TOTP generation/verification
- `qrcode[pil]>=7.4.0` - QR code generation
- `httpx-oauth>=0.15.0` - OAuth client

**Frontend (already in package.json):**

- TanStack Query - Data fetching
- TanStack Router - Routing
- Radix UI - Component primitives

**New runtime dependency:**

- None required

### 6.3 Migration Considerations

1. Run `app database make-migrations` after model changes
2. Run `app database upgrade` before deploying
3. Existing users will have MFA disabled by default
4. Existing sessions continue working (no forced re-login)
5. Railway pre-deploy command handles migrations automatically

### 6.4 Environment Variables

**Required for Railway deployment:**
```bash
# Auto-configured by deploy.sh
SECRET_KEY=<generated>
DATABASE_URL=${{Postgres.DATABASE_URL}}
APP_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}
PORT=8080
LITESTAR_PORT=8080

# Optional - configured via env-setup.sh
EMAIL_ENABLED=true
EMAIL_BACKEND=resend
EMAIL_FROM=noreply@yourdomain.com
RESEND_API_KEY=<your-key>

GOOGLE_OAUTH2_CLIENT_ID=<your-client-id>
GOOGLE_OAUTH2_CLIENT_SECRET=<your-client-secret>

GITHUB_OAUTH2_CLIENT_ID=<your-client-id>
GITHUB_OAUTH2_CLIENT_SECRET=<your-client-secret>
```

---

## 7. Rollout Plan

### Phase 1: Security Foundation

1. Implement CSRF protection middleware
2. Create RefreshToken model and migration
3. Implement refresh token rotation endpoint
4. Add refresh token service methods
5. Update login to issue token pair
6. **Tests required before proceeding**

### Phase 2: MFA System

1. Verify User model has MFA fields (add migration if needed)
2. Create MFA controller with enable/confirm/disable
3. Create MFA challenge controller
4. Update login flow for MFA detection
5. **Tests required before proceeding**

### Phase 3: Admin Domain

1. Create AuditLog model and migration
2. Create admin domain structure
3. Implement dashboard controller
4. Implement user management controller
5. Implement audit log controller
6. Wire up audit logging to key actions
7. **Tests required before proceeding**

### Phase 4: OAuth Enhancements

1. Add profile OAuth account endpoints
2. Implement account linking flow
3. Add OAuth token refresh background job
4. **Tests required before proceeding**

### Phase 5: Railway Deployment

1. Create deploy.sh script
2. Create env-setup.sh script
3. Create railway.json
4. Test deployment end-to-end
5. Document deployment process

### Phase 6: Frontend Implementation

1. MFA components (setup dialog, TOTP input, backup codes)
2. MFA challenge page
3. Profile MFA section
4. Profile connected accounts section
5. Admin layout and navigation
6. Admin dashboard page
7. Admin user management pages
8. Admin team management pages
9. Admin audit log page
10. Silent token refresh interceptor

### Phase 7: Final Validation

1. Run `make check-all`
2. Verify all acceptance criteria
3. Update TypeScript types with `make types`
4. Final security review

---

## 8. Detailed Implementation Specifications

### 8.1 Refresh Token Rotation Algorithm

The refresh token rotation system is critical for security. Here is the complete algorithm that must be implemented:

```python
async def rotate_refresh_token(
    self,
    current_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None
) -> tuple[str, str]:
    """Rotate refresh token and issue new token pair.

    This implements the OAuth 2.0 refresh token rotation pattern with
    reuse detection as recommended by the OAuth 2.1 specification.

    Args:
        current_token: The current refresh token presented by the client
        user_agent: Optional user agent string for device fingerprinting
        ip_address: Optional IP address for security logging

    Returns:
        Tuple of (new_access_token, new_refresh_token)

    Raises:
        TokenReuseDetectedError: If token was already used (security breach)
        TokenExpiredError: If token has expired
        TokenInvalidError: If token not found or malformed
    """
    # Step 1: Hash the incoming token
    token_hash = hashlib.sha256(current_token.encode()).hexdigest()

    # Step 2: Look up token in database
    db_token = await self.repository.get_one_or_none(token_hash=token_hash)

    if db_token is None:
        raise TokenInvalidError("Refresh token not found")

    # Step 3: Check for token reuse (CRITICAL SECURITY CHECK)
    if db_token.revoked_at is not None:
        # This token was already used and revoked!
        # This indicates either:
        # - Token theft and attacker is using stolen token
        # - Race condition with legitimate client
        # Either way, revoke the entire token family for safety
        await self._revoke_token_family(db_token.family_id)

        # Log security event
        self.logger.warning(
            "Refresh token reuse detected",
            family_id=str(db_token.family_id),
            user_id=str(db_token.user_id),
            ip_address=ip_address,
            original_revoked_at=db_token.revoked_at.isoformat()
        )

        raise TokenReuseDetectedError(
            "Refresh token has already been used. "
            "All sessions have been revoked for security."
        )

    # Step 4: Check expiration
    if db_token.expires_at < datetime.now(UTC):
        raise TokenExpiredError("Refresh token has expired")

    # Step 5: Revoke current token (mark as used)
    await self.repository.update(
        item_id=db_token.id,
        data={"revoked_at": datetime.now(UTC)}
    )

    # Step 6: Generate new token pair
    new_refresh_token = secrets.token_urlsafe(32)
    new_refresh_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()

    # Step 7: Store new refresh token (same family for reuse detection)
    await self.repository.add(
        RefreshToken(
            user_id=db_token.user_id,
            token_hash=new_refresh_hash,
            family_id=db_token.family_id,  # IMPORTANT: Same family
            expires_at=datetime.now(UTC) + timedelta(days=7),
            device_info=user_agent[:255] if user_agent else None
        )
    )

    # Step 8: Generate new access token
    user = await self.user_repository.get_one(id=db_token.user_id)
    new_access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        auth_method="refresh"
    )

    return new_access_token, new_refresh_token

async def _revoke_token_family(self, family_id: UUID) -> int:
    """Revoke all tokens in a family (used for security breach response).

    Returns:
        Number of tokens revoked
    """
    result = await self.repository.update_many(
        match_fields={"family_id": family_id, "revoked_at": None},
        data={"revoked_at": datetime.now(UTC)}
    )
    return result.rowcount
```

### 8.2 MFA Login Flow State Machine

The MFA login flow follows a strict state machine to prevent security bypasses:

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ POST /api/access/   │
│      login          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐    ┌─────────────────────┐
│ Password Valid?     │───▶│ Return 401          │
│                     │ No │ Invalid credentials │
└──────┬──────────────┘    └─────────────────────┘
       │ Yes
       ▼
┌─────────────────────┐    ┌─────────────────────┐
│ MFA Enabled?        │───▶│ Issue full JWT      │
│                     │ No │ access + refresh    │
└──────┬──────────────┘    └─────────────────────┘
       │ Yes
       ▼
┌─────────────────────┐
│ Issue MFA challenge │
│ token (5 min exp)   │
│ type: mfa_challenge │
│ aud: mfa_verify     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Frontend redirects  │
│ to /mfa-challenge   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ POST /api/mfa/      │
│ challenge/verify    │
│ + challenge_token   │
│ + TOTP or backup    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐    ┌─────────────────────┐
│ Code Valid?         │───▶│ Return 401          │
│                     │ No │ Increment attempts  │
└──────┬──────────────┘    └─────────────────────┘
       │ Yes
       ▼
┌─────────────────────┐
│ Issue full JWT      │
│ access + refresh    │
│ amr: [pwd, mfa]     │
└─────────────────────┘
```

### 8.3 Error Handling Specifications

All endpoints must return consistent error responses using this schema:

```python
class ErrorResponse(CamelizedBaseStruct):
    """Standard error response format."""
    error: str  # Machine-readable error code
    message: str  # Human-readable message
    details: dict | None = None  # Additional context

# Error codes for MFA endpoints
MFA_ERRORS = {
    "mfa_not_enabled": "MFA is not enabled on this account",
    "mfa_already_enabled": "MFA is already enabled",
    "mfa_not_confirmed": "MFA setup not confirmed yet",
    "invalid_totp_code": "Invalid verification code",
    "invalid_backup_code": "Invalid backup code",
    "no_backup_codes_remaining": "No backup codes remaining",
    "password_required": "Password confirmation required",
    "challenge_expired": "MFA challenge has expired",
    "challenge_invalid": "Invalid MFA challenge token",
}

# Error codes for refresh token endpoints
REFRESH_ERRORS = {
    "token_expired": "Refresh token has expired",
    "token_invalid": "Invalid refresh token",
    "token_reuse_detected": "Security violation: token reuse detected",
    "family_revoked": "All sessions have been revoked",
}

# Error codes for OAuth endpoints
OAUTH_ERRORS = {
    "provider_not_configured": "OAuth provider is not configured",
    "account_already_linked": "This account is already linked to another user",
    "cannot_unlink_only_auth": "Cannot unlink the only authentication method",
    "oauth_callback_failed": "OAuth callback failed",
    "token_exchange_failed": "Failed to exchange authorization code",
}
```

### 8.4 Rate Limiting Requirements

All authentication endpoints must implement rate limiting:

| Endpoint | Rate Limit | Window | Behavior |
|----------|------------|--------|----------|
| POST /api/access/login | 5 attempts | 15 min | Block IP |
| POST /api/mfa/challenge/verify | 5 attempts | 5 min | Lock account |
| POST /api/auth/refresh | 30 requests | 1 min | Throttle |
| POST /api/mfa/enable | 3 attempts | 1 hour | Block user |
| POST /api/access/forgot-password | 3 requests | 1 hour | Silently ignore |

### 8.5 Audit Log Event Types

The following events must be logged to the audit log:

| Action | Target Type | When Logged |
|--------|-------------|-------------|
| `user.login` | user | Successful login |
| `user.login_failed` | user | Failed login attempt |
| `user.logout` | user | User logout |
| `user.mfa_enabled` | user | MFA successfully enabled |
| `user.mfa_disabled` | user | MFA disabled |
| `user.password_changed` | user | Password updated |
| `user.password_reset` | user | Password reset completed |
| `user.email_verified` | user | Email verification completed |
| `user.created` | user | New user registered |
| `user.updated` | user | Admin updated user |
| `user.deactivated` | user | Admin deactivated user |
| `oauth.linked` | oauth_account | OAuth account linked |
| `oauth.unlinked` | oauth_account | OAuth account unlinked |
| `team.created` | team | New team created |
| `team.deleted` | team | Team deleted |
| `team.member_added` | team_member | Member joined team |
| `team.member_removed` | team_member | Member left/removed |
| `role.assigned` | user_role | Role assigned to user |
| `role.revoked` | user_role | Role removed from user |

### 8.6 Frontend Silent Refresh Implementation

The frontend must implement silent token refresh using TanStack Query's error handling:

```typescript
// lib/api/client.ts
import { QueryClient } from '@tanstack/react-query';

let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

async function refreshTokens(): Promise<void> {
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    credentials: 'include',  // Send cookies
    headers: {
      'X-CSRF-Token': getCsrfToken(),
    },
  });

  if (!response.ok) {
    // Refresh failed - redirect to login
    window.location.href = '/login?session_expired=true';
    throw new Error('Session expired');
  }
  // Cookies are automatically updated by the browser
}

export async function handleUnauthorized(): Promise<void> {
  // Prevent multiple concurrent refresh attempts
  if (isRefreshing) {
    return refreshPromise!;
  }

  isRefreshing = true;
  refreshPromise = refreshTokens()
    .finally(() => {
      isRefreshing = false;
      refreshPromise = null;
    });

  return refreshPromise;
}

// Configure QueryClient
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: async (failureCount, error) => {
        if (error instanceof Response && error.status === 401) {
          if (failureCount === 0) {
            try {
              await handleUnauthorized();
              return true;  // Retry the query
            } catch {
              return false;  // Don't retry
            }
          }
        }
        return failureCount < 3;
      },
    },
    mutations: {
      onError: async (error) => {
        if (error instanceof Response && error.status === 401) {
          await handleUnauthorized();
        }
      },
    },
  },
});
```

---

## 9. Critical Fixes (2025-12-29 Update)

This section documents critical fixes identified during implementation review.

### 9.1 Schema Naming Convention Fix

**Problem:** The SPA schemas use `Response` and `Request` suffixes, violating the Inertia pattern where schemas are named for what they represent.

**Required Renames:**

| Current Name | Correct Name | File Location |
|--------------|--------------|---------------|
| `MfaSetupResponse` | `MfaSetup` | `domain/accounts/schemas/` |
| `MfaConfirmRequest` | `MfaConfirm` | `domain/accounts/schemas/` |
| `MfaBackupCodesResponse` | `MfaBackupCodes` | `domain/accounts/schemas/` |
| `MfaDisableRequest` | `MfaDisable` | `domain/accounts/schemas/` |
| `MfaChallengeRequest` | `MfaChallenge` | `domain/accounts/schemas/` |
| `MfaChallengeResponse` | `MfaVerifyResult` | `domain/accounts/schemas/` |
| `MfaStatusResponse` | `MfaStatus` | `domain/accounts/schemas/` |
| `TokenRefreshResponse` | `TokenRefresh` | `domain/accounts/schemas/` |
| `ForgotPasswordResponse` | `PasswordResetSent` | `domain/accounts/schemas/` |
| `ResetPasswordResponse` | `PasswordResetComplete` | `domain/accounts/schemas/` |
| `ValidateResetTokenResponse` | `ResetTokenValidation` | `domain/accounts/schemas/` |
| `SessionsResponse` | `SessionList` | `domain/accounts/schemas/` |
| `OAuthAuthorizationResponse` | `OAuthAuthorization` | `domain/accounts/schemas/` |
| `LoginResponse` | **REMOVE** | Use `OAuth2Login` directly |

**Impact:**

- Update all controller return type annotations
- Update `signature_namespace` in route registrations
- Run `make types` to regenerate TypeScript client
- Update frontend API hooks

### 9.2 Frontend Validation Helpers

**Problem:** Auto-generated Zod schemas from OpenAPI are verbose and don't provide optimal form validation UX.

**Solution:** Create manual validation helpers at `src/js/src/lib/validation.ts`:

```typescript
// Key validation schemas to create:
export const passwordSchema = z.string()
  .min(8).max(100)
  .regex(/[A-Z]/).regex(/[a-z]/).regex(/[0-9]/);

export const emailSchema = z.string().email().max(255);
export const totpCodeSchema = z.string().length(6).regex(/^\d+$/);
export const recoveryCodeSchema = z.string().length(8).regex(/^[A-F0-9]+$/i);
export const usernameSchema = z.string().min(3).max(30).regex(/^[a-zA-Z0-9_-]+$/);

// Form schemas combining validations
export const loginFormSchema = z.object({ email: emailSchema, password: z.string().min(1) });
export const mfaSetupFormSchema = z.object({ code: totpCodeSchema });
```

**Note:** Keep generated Zod schemas for API type safety. Use manual schemas for form validation.

### 9.3 React Email Templates

**Status:** React Email templates exist in the SPA and compile to static HTML for backend delivery.

**Directory Structure:**
```
src/js/templates/
├── src/
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── Button.tsx
│   └── emails/
│       ├── email-verification.tsx
│       ├── password-reset.tsx
│       ├── password-reset-confirmation.tsx
│       ├── welcome.tsx
│       └── team-invitation.tsx
├── build-emails.ts
└── package.json
```

**Build Process:**

1. Templates use placeholder syntax: `{{VARIABLE_NAME}}`
2. Build script renders React to static HTML
3. Output goes to `src/py/app/server/static/email/`
4. Backend replaces placeholders at runtime

**npm script:** `"build:emails": "bun run src/templates/build-emails.ts"`

### 9.4 Already Correct (Verified)

The following patterns are already correctly implemented:

- ✅ **Deferred Security Groups**: User model has `deferred_group="security_sensitive"` on `hashed_password`, `totp_secret`, `backup_codes`
- ✅ **Advanced Alchemy Service Hooks**: Services implement `to_model_on_create`, `to_model_on_update`, `to_model_on_upsert`
- ✅ **Service Provider Pattern**: Uses `create_service_provider` with eager loading
- ✅ **Inner Repository Pattern**: Services define inner `Repo` class

---

## 10. Open Questions

None - All architectural decisions resolved through multi-model consensus.

---

## 11. Appendix

### A. Critical Fix Reference Files

**Schema naming reference:**

- `/home/cody/code/litestar/litestar-fullstack-inertia/app/domain/accounts/schemas/` - Correct naming pattern

**React email template reference:**

- `/home/cody/code/g/dma/accelerator/src/js/templates/` - Template structure and build script

**Detailed analysis:**

- `specs/active/inertia-spa-parity/research/critical-fixes.md` - Full research documentation

### B. Multi-Model Consensus Summary

**Models consulted:** Gemini 3 Pro (for JWT), GPT 5.2 (against/challenging)

**Unanimous agreements:**

1. HTTP-only cookies required (not localStorage)
2. CSRF protection mandatory
3. Refresh token rotation with reuse detection required
4. Hashed token storage required
5. MFA challenge token approach secure if properly scoped
6. OAuth tokens encrypted at rest required

**Final decision:** Keep JWT with HTTP-only cookies, implement all security enhancements

**Confidence:** 8.5/10 (high)

### C. Reference Files

**Inertia implementations to reference:**

- `/home/cody/code/litestar/litestar-fullstack-inertia/app/domain/accounts/controllers/_mfa.py`
- `/home/cody/code/litestar/litestar-fullstack-inertia/app/domain/accounts/controllers/_mfa_challenge.py`
- `/home/cody/code/litestar/litestar-fullstack-inertia/app/domain/admin/controllers/_dashboard.py`
- `/home/cody/code/litestar/litestar-fullstack-inertia/tools/deploy/railway/deploy.sh`
- `/home/cody/code/litestar/litestar-fullstack-inertia/tools/deploy/railway/env-setup.sh`

### D. Existing SPA Code to Extend

- `src/py/app/lib/crypt.py` - Has TOTP functions ready to use
- `src/py/app/domain/accounts/services/_user_oauth_account.py` - Extend for linking
- `src/py/app/domain/accounts/controllers/_oauth.py` - Extend for profile linking
- `src/py/app/domain/accounts/guards.py` - Has `requires_superuser` guard

---

**Document Status:** Complete and ready for implementation
**Next Step:** Run `/implement inertia-spa-parity` to begin Phase 1
