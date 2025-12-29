# Research: Litestar Fullstack Inertia to SPA Parity

## Executive Summary

This research document analyzes the differences between the `litestar-fullstack-inertia` project and the `litestar-fullstack-spa` project to identify all changes required to achieve feature parity. The SPA version should provide identical functionality using client-side React/TanStack architecture instead of Inertia.js server-side rendering.

**Complexity Assessment: COMPLEX (10+ implementation phases)**

The analysis covers: Railway deployment tooling, OAuth2 integrations with refresh tokens, MFA/TOTP authentication, password reset flows, email templates, admin domain, and authentication architecture decisions validated through multi-model AI consensus.

---

## 1. Project Architecture Comparison

### 1.1 Backend Structure

| Aspect | Inertia Project | SPA Project | Gap |
|--------|-----------------|-------------|-----|
| Root path | `app/` | `src/py/app/` | Different structure |
| Frontend path | `resources/` | `src/js/src/` | Different structure |
| Routing | Inertia.js (server-driven) | TanStack Router (client-driven) | Architectural difference |
| Authentication | Server sessions | JWT + HTTP-only cookies | Requires adaptation |
| Flash messages | Inertia flash system | TanStack Query cache | Different approach |

### 1.2 Domain Coverage

**Inertia Project Domains:**
- `accounts/` - User management, OAuth, MFA, password reset
- `admin/` - Dashboard, user/team management, audit logs
- `tags/` - Tag management
- `teams/` - Team management with invitations
- `web/` - Static pages (Inertia-specific)

**SPA Project Domains:**
- `accounts/` - User management, OAuth (partial), password reset
- `system/` - Health checks, background jobs
- `tags/` - Tag management
- `teams/` - Team management with invitations

**Missing in SPA:** `admin/` domain entirely, MFA controllers, complete OAuth account management

---

## 2. Authentication Architecture Analysis

### 2.1 Multi-Model Consensus Results

A consensus analysis was conducted with **Gemini 3 Pro** (advocating for JWT) and **GPT 5.2** (challenging with security concerns) to determine the optimal authentication architecture.

#### Points of Agreement (UNANIMOUS):

1. **HTTP-only cookies are required** - Never store tokens in localStorage (XSS protection)
2. **CSRF protection is mandatory** - Cookies automatically sent by browsers require CSRF defense
3. **Refresh token rotation is essential** - Short-lived access tokens (15 min) with rotating refresh tokens (7 days)
4. **Reuse detection required** - If old refresh token is presented after rotation, revoke entire token family
5. **Hashed token storage** - Store refresh tokens as SHA-256 hashes, never plaintext
6. **MFA challenge token approach is secure** - IF strictly scoped to MFA verification endpoint only
7. **OAuth tokens encrypted at rest** - Provider tokens stored encrypted in database

#### Points of Divergence:

| Factor | Gemini 3 Pro | GPT 5.2 |
|--------|-------------|---------|
| Primary recommendation | JWT + HTTP-only cookies | Sessions simpler for browser-only |
| Rationale | Scalability, multi-client support | Lower complexity, built-in revocation |
| Confidence | 9/10 | 8/10 |

#### Final Decision: **Keep JWT with Enhanced Security**

The SPA already uses JWT with HTTP-only cookies. Converting to sessions would require significant refactoring and add Redis dependency. However, we must implement all agreed security enhancements.

### 2.2 Token Architecture Specification

#### Access Token (15-minute expiry)
```
Cookie: access_token
HttpOnly: true
Secure: true
SameSite: Lax
Path: /

Claims:
- sub: user_id
- email: user email
- is_superuser: boolean
- is_verified: boolean
- auth_method: "password" | "oauth" | "mfa"
- amr: ["pwd"] | ["pwd", "mfa"]  # Authentication methods reference
- exp: 15 minutes from now
- jti: unique token ID
```

#### Refresh Token (7-day expiry)
```
Cookie: refresh_token
HttpOnly: true
Secure: true
SameSite: Strict  # Stricter than access
Path: /api/auth/refresh  # Tight path scoping

Database Model:
- token_hash: SHA-256 hash
- family_id: UUID for reuse detection
- user_id: foreign key
- expires_at: datetime
- revoked_at: datetime | null
- device_info: optional fingerprint
```

#### MFA Challenge Token (5-minute expiry)
```
NOT stored in cookie - returned in response body

Claims:
- sub: user_id
- email: user email
- type: "mfa_challenge"  # Distinct type
- aud: "mfa_verification"  # Strict audience
- amr: ["pwd"]  # Password verified, MFA pending
- exp: 5 minutes from now
- jti: unique challenge ID
```

### 2.3 Refresh Token Rotation Flow

1. User presents refresh token to `/api/auth/refresh`
2. Server hashes token and looks up in database
3. **Reuse detection**: If token already revoked, revoke ENTIRE family (security breach)
4. If valid, revoke current token and issue new pair
5. New refresh token gets same `family_id` (for future reuse detection)
6. Return new access token (in cookie) + new refresh token (in cookie)

### 2.4 MFA Challenge Flow (Stateless)

1. `POST /api/access/login` with credentials
2. If user has MFA enabled:
   - Return `{ mfa_required: true, challenge_token: "..." }` (NOT full auth)
   - Frontend redirects to `/mfa-challenge`
3. `POST /api/mfa/challenge/verify` with challenge_token + TOTP code
4. Verify challenge token (audience, type, expiry)
5. Verify TOTP/backup code
6. Issue full auth tokens with `amr: ["pwd", "mfa"]`

---

## 3. Feature Gap Analysis

### 3.1 Railway Deployment Tools (ENTIRELY MISSING)

The Inertia project includes comprehensive Railway deployment automation that the SPA lacks:

**Files to create:**
- `tools/deploy/railway/deploy.sh` (~480 lines)
  - Railway CLI installation and authentication
  - Project creation and linking
  - PostgreSQL database provisioning
  - App service setup with domain generation
  - Environment variable configuration
  - Metal builds enablement
  - Deployment with health checks

- `tools/deploy/railway/env-setup.sh` (~375 lines)
  - Interactive environment configuration menu
  - Resend email setup wizard
  - GitHub/Google OAuth configuration
  - Load from .env file capability
  - Individual variable setting

- `railway.json` (~35 lines)
  - Dockerfile.distroless builder configuration
  - Deploy runtime V2 settings
  - Health check path and timeout
  - Pre-deploy database migrations
  - CPU/memory limits (2 CPU, 2GB RAM)
  - Multi-region configuration

### 3.2 MFA/TOTP System (ENTIRELY MISSING)

**Backend Components:**

Controllers needed:
- `_mfa.py` - MFA management
  - `POST /api/mfa/enable` - Generate TOTP secret + QR code
  - `POST /api/mfa/confirm` - Verify code, enable MFA, return backup codes
  - `DELETE /api/mfa/disable` - Disable MFA (requires password)
  - `POST /api/mfa/regenerate-codes` - Generate new backup codes

- `_mfa_challenge.py` - Login flow MFA verification
  - `POST /api/mfa/challenge/verify` - Verify TOTP/backup during login

Schemas needed:
- `MfaSetup` - secret + qr_code (base64 PNG)
- `MfaConfirm` - 6-digit code input
- `MfaBackupCodes` - list of plain codes (shown once)
- `MfaDisable` - password confirmation
- `MfaChallengeRequest` - code or recovery_code
- `MfaChallengeResponse` - verified, token, used_backup_code, remaining_codes

**User Model Fields Required:**
```python
totp_secret: Mapped[str | None]  # EncryptedString
is_two_factor_enabled: Mapped[bool] = False
two_factor_confirmed_at: Mapped[datetime | None]
backup_codes: Mapped[list | None]  # JSONB of hashed codes
```

**Existing Infrastructure:**
The SPA already has `crypt.py` with TOTP functions:
- `generate_totp_secret()`
- `verify_totp_code()`
- `get_totp_provisioning_uri()`
- `generate_totp_qr_code()`
- `generate_backup_codes()`
- `hash_backup_codes()`
- `verify_backup_code()`

### 3.3 Admin Domain (ENTIRELY MISSING)

**New domain structure:** `src/py/app/domain/admin/`

Files to create:
- `__init__.py` - Domain exports
- `dependencies.py` - `provide_audit_service`
- `schemas.py` - Admin DTOs
- `controllers/__init__.py` - Controller exports
- `controllers/_dashboard.py` - Statistics and overview
- `controllers/_users.py` - User CRUD management
- `controllers/_teams.py` - Team management
- `controllers/_audit.py` - Audit log viewing
- `services/__init__.py` - Service exports
- `services/_audit.py` - AuditLogService

**New database model:** `src/py/app/db/models/audit_log.py`
```python
class AuditLog(UUIDAuditBase):
    __tablename__ = "audit_log"

    actor_id: Mapped[UUID | None]  # Who performed action
    actor_email: Mapped[str]
    action: Mapped[str]  # "user.created", "team.deleted"
    target_type: Mapped[str | None]  # "user", "team"
    target_id: Mapped[UUID | None]
    target_label: Mapped[str | None]  # Human readable
    details: Mapped[dict | None]  # JSONB
    ip_address: Mapped[str | None]
```

### 3.4 OAuth Account Management (PARTIAL)

**Current SPA state:**
- OAuth login works (Google, GitHub)
- Stateless JWT-based state tokens
- Creates users on first OAuth login
- Basic `UserOAuthAccountService` exists

**Missing features:**
1. Profile OAuth account listing endpoint
2. Account linking from authenticated profile
3. Account unlinking with validation
4. Scope upgrade flow
5. OAuth provider token refresh (background job)

**Endpoints to add:**
- `GET /api/profile/oauth/accounts` - List linked accounts
- `POST /api/profile/oauth/{provider}/link` - Start linking
- `GET /api/profile/oauth/{provider}/complete` - Complete linking
- `DELETE /api/profile/oauth/{provider}` - Unlink account
- `POST /api/profile/oauth/{provider}/upgrade-scopes` - Request more permissions

### 3.5 Refresh Token System (NEW)

**New database model:** `src/py/app/db/models/refresh_token.py`
```python
class RefreshToken(UUIDAuditBase):
    __tablename__ = "refresh_token"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_account.id"))
    token_hash: Mapped[str]  # SHA-256, never plaintext
    family_id: Mapped[UUID]  # For reuse detection
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    device_info: Mapped[str | None]
```

**New service methods:**
- `create_refresh_token(user_id, family_id=None)`
- `validate_refresh_token(token_hash)`
- `rotate_refresh_token(old_token)`
- `revoke_token_family(family_id)`
- `cleanup_expired_tokens()` (background job)

### 3.6 Email Templates (EQUIVALENT)

Both projects have email templates, but use different systems:
- **Inertia**: Custom `{{PLACEHOLDER}}` template system
- **SPA**: Jinja2 templates (`.j2` files)

**SPA templates exist and are complete:**
- `email_verification.html.j2` / `.txt.j2`
- `password_reset.html.j2` / `.txt.j2`
- `password_reset_confirmation.html.j2` / `.txt.j2`
- `team_invitation.html.j2` / `.txt.j2`
- `welcome.html.j2` / `.txt.j2`

**No changes needed** - Jinja2 templates are more maintainable.

---

## 4. Frontend Gap Analysis

### 4.1 Missing Pages

**Auth pages:**
- `routes/_public/mfa-challenge.tsx` - MFA verification during login

**Profile pages (modifications):**
- MFA section in profile settings
- Connected accounts section

**Admin pages (NEW route group):**
- `routes/_app/admin/index.tsx` - Dashboard with stats
- `routes/_app/admin/users/index.tsx` - User list
- `routes/_app/admin/users/$userId.tsx` - User detail
- `routes/_app/admin/teams/index.tsx` - Team list
- `routes/_app/admin/teams/$teamId.tsx` - Team detail
- `routes/_app/admin/audit.tsx` - Audit log

### 4.2 New Components Needed

**MFA components:**
- `mfa-setup-dialog.tsx` - QR code display + verification
- `mfa-disable-dialog.tsx` - Password confirmation
- `backup-codes-display.tsx` - One-time code display
- `totp-input.tsx` - 6-digit code input

**Profile components:**
- `mfa-section.tsx` - MFA settings card
- `connected-accounts.tsx` - OAuth accounts list
- `oauth-link-button.tsx` - Provider link buttons

**Admin components:**
- `stats-cards.tsx` - Dashboard statistics
- `recent-activity.tsx` - Activity feed
- `user-table.tsx` - User management DataTable
- `team-table.tsx` - Team management DataTable
- `audit-log-table.tsx` - Filterable audit entries

### 4.3 TanStack Query Hooks

```typescript
// MFA hooks
useMfaStatus()
useMfaEnable()
useMfaConfirm()
useMfaDisable()
useRegenerateBackupCodes()
useMfaChallenge()

// OAuth profile hooks
useOAuthAccounts()
useLinkOAuth()
useUnlinkOAuth()

// Admin hooks
useAdminStats()
useAdminUsers()
useAdminUser(userId)
useAdminTeams()
useAdminTeam(teamId)
useAuditLog()
```

### 4.4 Silent Token Refresh

Frontend needs response interceptor for seamless token refresh:

```typescript
// TanStack Query global error handler
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error.status === 401 && failureCount === 0) {
          // Attempt silent refresh
          return true;
        }
        return false;
      },
    },
  },
});

// API client interceptor
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true;
      await refreshTokens();
      return api(error.config);
    }
    return Promise.reject(error);
  }
);
```

---

## 5. Database Migrations Required

### 5.1 New Tables

1. **audit_log** - Admin audit trail
2. **refresh_token** - Token rotation tracking

### 5.2 User Model Updates

Verify these fields exist (add migration if missing):
- `totp_secret` - EncryptedString
- `is_two_factor_enabled` - boolean default false
- `two_factor_confirmed_at` - datetime nullable
- `backup_codes` - JSONB nullable

---

## 6. Security Considerations

### 6.1 CSRF Protection (MANDATORY)

Since cookies are used for authentication, CSRF protection is required:

```python
from litestar.middleware.csrf import CSRFConfig

csrf_config = CSRFConfig(
    secret=settings.SECRET_KEY,
    cookie_name="csrf_token",
    cookie_secure=True,
    cookie_samesite="lax",
    header_name="X-CSRF-Token",
    safe_methods={"GET", "HEAD", "OPTIONS"}
)
```

Frontend must read CSRF token from cookie and include in `X-CSRF-Token` header for all mutations.

### 6.2 Refresh Token Security

- Store hashed (SHA-256), never plaintext
- Use `SameSite=Strict` (stricter than access token)
- Scope to specific path: `Path=/api/auth/refresh`
- Implement reuse detection with family revocation
- Background job to cleanup expired tokens

### 6.3 MFA Token Security

- Distinct `type` claim: `"mfa_challenge"`
- Strict `aud` claim: `"mfa_verification"`
- Very short expiry: 5 minutes
- Only accepted by MFA verification endpoint
- Include `amr` claim for authentication method tracking

---

## 7. Implementation Priority

### Phase 1: Security Foundation (HIGH PRIORITY)
1. Refresh token system with rotation
2. CSRF protection configuration
3. MFA challenge token flow

### Phase 2: Railway Deployment (HIGH PRIORITY)
1. deploy.sh script
2. env-setup.sh script
3. railway.json configuration

### Phase 3: MFA System (HIGH PRIORITY)
1. MFA controllers
2. MFA schemas
3. User model updates
4. Frontend MFA components

### Phase 4: Admin Domain (MEDIUM PRIORITY)
1. Audit log model
2. Admin controllers
3. Admin services
4. Frontend admin pages

### Phase 5: OAuth Enhancements (MEDIUM PRIORITY)
1. Profile account linking
2. OAuth token refresh background job
3. Frontend connected accounts UI

### Phase 6: Frontend Polish (LOWER PRIORITY)
1. Silent token refresh interceptor
2. Admin layout and navigation
3. MFA status indicators

---

## 8. Conclusion

This analysis identifies approximately **15 new files** and **8 modified files** required to achieve feature parity with the Inertia version. The most significant additions are:

1. **Railway deployment tooling** - Complete automation missing
2. **MFA/TOTP system** - Controllers and frontend missing
3. **Admin domain** - Entirely missing
4. **Refresh token system** - New security requirement from consensus
5. **OAuth account management** - Profile linking/unlinking missing

The authentication architecture decision to keep JWT with HTTP-only cookies was validated by multi-model consensus, with the requirement to implement refresh token rotation, CSRF protection, and proper MFA challenge token scoping.

Total estimated effort: **Complex implementation** requiring careful attention to security requirements and phased delivery.
