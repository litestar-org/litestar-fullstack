# Task Breakdown: Litestar Fullstack Inertia to SPA Parity

**PRD Reference:** `specs/active/inertia-spa-parity/prd.md`
**Research Reference:** `specs/active/inertia-spa-parity/research/plan.md`
**Critical Fixes Reference:** `specs/active/inertia-spa-parity/research/critical-fixes.md`

---

## Phase 0: Critical Pattern Fixes (PRIORITY)

> **IMPORTANT:** Complete these fixes before continuing with other phases. These ensure pattern compliance with the Inertia reference implementation.

### 0.1 Schema Naming Convention Fix ✅ COMPLETED
- [x] Rename `MfaSetupResponse` to `MfaSetup` in `domain/accounts/schemas.py`
- [x] Rename `MfaConfirmRequest` to `MfaConfirm` in `domain/accounts/schemas.py`
- [x] Rename `MfaBackupCodesResponse` to `MfaBackupCodes` in `domain/accounts/schemas.py`
- [x] Rename `MfaDisableRequest` to `MfaDisable` in `domain/accounts/schemas.py`
- [x] Rename `MfaChallengeRequest` to `MfaChallenge` in `domain/accounts/schemas.py`
- [x] Rename `MfaChallengeResponse` to `MfaVerifyResult` in `domain/accounts/schemas.py`
- [x] Rename `MfaStatusResponse` to `MfaStatus` in `domain/accounts/schemas.py`
- [x] Rename `TokenRefreshResponse` to `TokenRefresh` in `domain/accounts/schemas.py`
- [x] Rename `ForgotPasswordResponse` to `PasswordResetSent` in `domain/accounts/schemas.py`
- [x] Rename `ResetPasswordResponse` to `PasswordResetComplete` in `domain/accounts/schemas.py`
- [x] Rename `ValidateResetTokenResponse` to `ResetTokenValidation` in `domain/accounts/schemas.py`
- [x] Rename `SessionsResponse` to `SessionList` in `domain/accounts/schemas.py`
- [x] Rename `OAuthAuthorizationResponse` to `OAuthAuthorization` in `domain/accounts/schemas.py`
- [x] Update all controller return type annotations to use new names
- [x] Update `__all__` exports in schemas.py
- [x] Run `make types` to regenerate TypeScript client
- [x] Fixed frontend API client for hey-api fetch-based API (baseUrl, credentials)
- [x] Fixed interceptor API from axios to fetch pattern

**Files modified:**
- `src/py/app/domain/accounts/schemas.py`
- `src/py/app/domain/admin/schemas.py`
- `src/py/app/domain/accounts/controllers/_access.py`
- `src/py/app/domain/accounts/controllers/_mfa.py`
- `src/py/app/domain/accounts/controllers/_mfa_challenge.py`
- `src/py/app/domain/accounts/controllers/_oauth.py`
- `src/js/web/src/main.tsx`
- `src/js/web/src/lib/auth.ts`
- `src/js/web/src/components/auth/user-signup-form.tsx`

### 0.2 Frontend Validation Helpers ✅ COMPLETED
- [x] Create `src/js/web/src/lib/validation.ts`
- [x] Add `passwordSchema` with proper strength requirements
- [x] Add `emailSchema` with format validation
- [x] Add `totpCodeSchema` (6 digits)
- [x] Add `recoveryCodeSchema` (8 hex chars)
- [x] Add `usernameSchema` with character restrictions
- [x] Add `loginFormSchema` composite
- [x] Add `registerFormSchema` with password confirmation
- [x] Add `mfaSetupFormSchema`
- [x] Add `mfaChallengeFormSchema` (union type)
- [x] Update login form to use new validation schemas

**Files created:**
- `src/js/web/src/lib/validation.ts`

**Files modified:**
- `src/js/web/src/components/auth/user-login-form.tsx`

### 0.2.5 JS Directory Reorganization ✅ COMPLETED
- [x] Move web app from `src/js/` to `src/js/web/`
- [x] Create `src/js/templates/` for email templates
- [x] Update Makefile paths (install, upgrade, clean, fix)
- [x] Update `.pre-commit-config.yaml` biome path
- [x] Update `pyproject.toml` (bumpversion, codespell skip)
- [x] Update `.gitignore` paths
- [x] Update Python vite plugin settings (`settings.py`)
- [x] Update Dockerfiles (Dockerfile, Dockerfile.dev, Dockerfile.distroless)
- [x] Update `tools/manage_assets.py` to use bun
- [x] Update `AGENTS.md` project structure

**Files modified:**
- `Makefile`
- `.pre-commit-config.yaml`
- `pyproject.toml`
- `.gitignore`
- `src/py/app/lib/settings.py`
- `tools/deploy/docker/Dockerfile`
- `tools/deploy/docker/Dockerfile.dev`
- `tools/deploy/docker/Dockerfile.distroless`
- `tools/manage_assets.py`
- `AGENTS.md`

### 0.3 React Email Template Setup ✅ COMPLETED
- [x] Create `src/js/templates/` directory structure
- [x] Create `src/js/templates/package.json` with React/Bun dependencies
- [x] Create `src/js/templates/tsconfig.json`
- [x] Create `src/js/templates/src/components/Layout.tsx`
- [x] Create `src/js/templates/src/components/Header.tsx`
- [x] Create `src/js/templates/src/components/Footer.tsx`
- [x] Create `src/js/templates/src/components/Button.tsx`
- [x] Create `src/js/templates/src/components/index.ts`
- [x] Create `src/js/templates/src/emails/email-verification.tsx`
- [x] Create `src/js/templates/src/emails/password-reset.tsx`
- [x] Create `src/js/templates/src/emails/welcome.tsx`
- [x] Create `src/js/templates/src/emails/team-invitation.tsx`
- [x] Create `src/js/templates/build-emails.ts` build script
- [x] Update Makefile with `make build-emails` target
- [x] Create output directory `src/py/app/templates/email/`
- [x] Build and verify HTML output (4 templates built)
- [x] Update .gitignore for email template artifacts

**Files created:**
- `src/js/templates/package.json`
- `src/js/templates/tsconfig.json`
- `src/js/templates/build-emails.ts`
- `src/js/templates/src/components/Layout.tsx`
- `src/js/templates/src/components/Header.tsx`
- `src/js/templates/src/components/Footer.tsx`
- `src/js/templates/src/components/Button.tsx`
- `src/js/templates/src/components/index.ts`
- `src/js/templates/src/emails/email-verification.tsx`
- `src/js/templates/src/emails/password-reset.tsx`
- `src/js/templates/src/emails/welcome.tsx`
- `src/js/templates/src/emails/team-invitation.tsx`

**Files modified:**
- `Makefile`
- `.gitignore`

### 0.3.5 Build System & Docker Updates ✅ COMPLETED
- [x] Fix Makefile `build-emails` command (shell context)
- [x] Update Dockerfile with email templates build process
- [x] Update Dockerfile.distroless with email templates build process
- [x] Update Dockerfile.dev with email templates build process
- [x] Add `force-include` to pyproject.toml for wheel assets
- [x] Add email templates to wheel package
- [x] Verify wheel contains Python code, public assets, and email templates (689 files)

**Files modified:**
- `Makefile`
- `tools/deploy/docker/Dockerfile`
- `tools/deploy/docker/Dockerfile.dev`
- `tools/deploy/docker/Dockerfile.distroless`
- `pyproject.toml`

### 0.4 Verify Existing Patterns (No Changes Needed)
- [x] Verify User model has `deferred_group="security_sensitive"` on sensitive fields
- [x] Verify services use `to_model_on_create`, `to_model_on_update` hooks
- [x] Verify `create_service_provider` pattern is used correctly
- [x] Verify inner repository pattern in services

---

## Phase 1: Security Foundation

### 1.1 CSRF Protection Configuration
- [ ] Add CSRFConfig to Litestar application configuration
- [ ] Configure cookie settings (secure, samesite=lax, httponly)
- [ ] Add X-CSRF-Token header to frontend API client
- [ ] Update frontend to read CSRF token from cookie
- [ ] Add CSRF exempt paths for OAuth callbacks
- [ ] Write integration tests for CSRF protection

**Files to modify:**
- `src/py/app/server/plugins.py` - Add CSRFConfig
- `src/js/web/src/lib/api/client.ts` - Add CSRF header interceptor

### 1.2 Refresh Token Database Model
- [ ] Create `RefreshToken` model in `src/py/app/db/models/refresh_token.py`
- [ ] Add fields: token_hash, family_id, user_id, expires_at, revoked_at, device_info
- [ ] Add relationship to User model
- [ ] Create database migration
- [ ] Add model to `__init__.py` exports

**Files to create:**
- `src/py/app/db/models/refresh_token.py`

**Files to modify:**
- `src/py/app/db/models/__init__.py`

### 1.3 Refresh Token Service
- [ ] Create `RefreshTokenService` with inner Repo pattern
- [ ] Implement `create_refresh_token(user_id, family_id=None)`
- [ ] Implement `validate_refresh_token(token_hash)`
- [ ] Implement `rotate_refresh_token(old_token)` with reuse detection
- [ ] Implement `revoke_token_family(family_id)`
- [ ] Implement `cleanup_expired_tokens()` for background job
- [ ] Add dependency provider function
- [ ] Write unit tests for token rotation logic
- [ ] Write unit tests for reuse detection

**Files to create:**
- `src/py/app/domain/accounts/services/_refresh_token.py`

**Files to modify:**
- `src/py/app/domain/accounts/services/__init__.py`
- `src/py/app/domain/accounts/dependencies.py`

### 1.4 Auth Token Flow Updates
- [ ] Update access token to include `jti`, `amr` claims
- [ ] Add refresh token endpoint `POST /api/auth/refresh`
- [ ] Configure refresh token cookie (SameSite=Strict, Path=/api/auth/refresh)
- [ ] Update login to issue both access and refresh tokens
- [ ] Update logout to revoke refresh token family
- [ ] Add background job for expired token cleanup
- [ ] Write integration tests for token refresh flow

**Files to modify:**
- `src/py/app/domain/accounts/controllers/_access.py`
- `src/py/app/lib/jwt.py` (or create if needed)

### 1.5 Frontend Silent Refresh
- [ ] Create response interceptor for 401 handling
- [ ] Implement silent refresh with retry logic
- [ ] Add request queue during refresh
- [ ] Handle concurrent refresh attempts
- [ ] Redirect to login on refresh failure
- [ ] Write E2E tests for token expiry handling

**Files to modify:**
- `src/js/web/src/lib/api/client.ts`
- `src/js/web/src/providers/auth-provider.tsx`

---

## Phase 2: MFA System

### 2.1 User Model MFA Fields
- [ ] Add `totp_secret` field (EncryptedString)
- [ ] Add `is_two_factor_enabled` field (boolean, default false)
- [ ] Add `two_factor_confirmed_at` field (datetime nullable)
- [ ] Add `backup_codes` field (JSONB nullable)
- [ ] Create database migration
- [ ] Verify existing TOTP functions in `crypt.py` work correctly

**Files to modify:**
- `src/py/app/db/models/user.py`

### 2.2 MFA Schemas
- [ ] Create `MfaSetup` schema (secret, qr_code base64)
- [ ] Create `MfaConfirm` schema (code input)
- [ ] Create `MfaBackupCodes` schema (list of codes)
- [ ] Create `MfaDisable` schema (password confirmation)
- [ ] Create `MfaChallengeRequest` schema (code or recovery_code)
- [ ] Create `MfaChallengeResponse` schema (verified, token, used_backup_code, remaining)

**Files to create:**
- `src/py/app/domain/accounts/schemas/_mfa.py`

**Files to modify:**
- `src/py/app/domain/accounts/schemas/__init__.py`

### 2.3 MFA Management Controller
- [ ] Create `MfaController` at `/api/mfa`
- [ ] Implement `POST /api/mfa/enable` - Generate TOTP secret + QR code
- [ ] Implement `POST /api/mfa/confirm` - Verify code, enable MFA, return backup codes
- [ ] Implement `DELETE /api/mfa/disable` - Disable MFA (requires password)
- [ ] Implement `POST /api/mfa/regenerate-codes` - Generate new backup codes
- [ ] Add rate limiting (5 attempts per 15 minutes)
- [ ] Write unit tests for each endpoint
- [ ] Write integration tests for full MFA setup flow

**Files to create:**
- `src/py/app/domain/accounts/controllers/_mfa.py`

**Files to modify:**
- `src/py/app/domain/accounts/controllers/__init__.py`

### 2.4 MFA Challenge Controller
- [ ] Create `MfaChallengeController` at `/api/mfa/challenge`
- [ ] Implement `POST /api/mfa/challenge/verify` - Verify TOTP/backup during login
- [ ] Validate challenge token (type, audience, expiry)
- [ ] Issue full auth tokens with `amr: ["pwd", "mfa"]`
- [ ] Track backup code usage
- [ ] Write integration tests for challenge flow

**Files to create:**
- `src/py/app/domain/accounts/controllers/_mfa_challenge.py`

### 2.5 Login Flow MFA Integration
- [ ] Update login to check `is_two_factor_enabled`
- [ ] Return `mfa_required: true` with challenge token when MFA enabled
- [ ] Create MFA challenge token with strict scope
- [ ] Update login response schema

**Files to modify:**
- `src/py/app/domain/accounts/controllers/_access.py`
- `src/py/app/domain/accounts/schemas/_access.py`

### 2.6 Frontend MFA Components
- [ ] Create `totp-input.tsx` - 6-digit code input component
- [ ] Create `mfa-setup-dialog.tsx` - QR code display + verification
- [ ] Create `mfa-disable-dialog.tsx` - Password confirmation dialog
- [ ] Create `backup-codes-display.tsx` - One-time code display
- [ ] Create `mfa-section.tsx` - MFA settings card for profile

**Files to create:**
- `src/js/web/src/components/mfa/totp-input.tsx`
- `src/js/web/src/components/mfa/mfa-setup-dialog.tsx`
- `src/js/web/src/components/mfa/mfa-disable-dialog.tsx`
- `src/js/web/src/components/mfa/backup-codes-display.tsx`
- `src/js/web/src/components/profile/mfa-section.tsx`

### 2.7 Frontend MFA Pages
- [ ] Create `mfa-challenge.tsx` route in `_public/`
- [ ] Add MFA section to profile settings page
- [ ] Create TanStack Query hooks for MFA operations
- [ ] Handle MFA challenge redirect in login flow

**Files to create:**
- `src/js/web/src/routes/_public/mfa-challenge.tsx`

**Files to modify:**
- `src/js/web/src/routes/_app/profile/index.tsx`
- `src/js/web/src/lib/api/hooks/auth.ts`

---

## Phase 3: Admin Domain

### 3.1 Audit Log Model
- [ ] Create `AuditLog` model in `src/py/app/db/models/audit_log.py`
- [ ] Add fields: actor_id, actor_email, action, target_type, target_id, target_label, details, ip_address
- [ ] Create database migration
- [ ] Add model to exports

**Files to create:**
- `src/py/app/db/models/audit_log.py`

**Files to modify:**
- `src/py/app/db/models/__init__.py`

### 3.2 Audit Log Service
- [ ] Create `AuditLogService` with inner Repo pattern
- [ ] Implement `log_action()` method
- [ ] Implement `get_user_activity()` method
- [ ] Implement `get_recent_activity()` method
- [ ] Add helper functions for common audit events
- [ ] Write unit tests

**Files to create:**
- `src/py/app/domain/admin/services/_audit.py`
- `src/py/app/domain/admin/services/__init__.py`

### 3.3 Admin Domain Structure
- [ ] Create `src/py/app/domain/admin/` directory
- [ ] Create `__init__.py` with domain exports
- [ ] Create `dependencies.py` with provider functions
- [ ] Create `schemas.py` with admin DTOs

**Files to create:**
- `src/py/app/domain/admin/__init__.py`
- `src/py/app/domain/admin/dependencies.py`
- `src/py/app/domain/admin/schemas.py`

### 3.4 Admin Dashboard Controller
- [ ] Create `DashboardController` at `/api/admin/dashboard`
- [ ] Implement `GET /api/admin/dashboard/stats` - System statistics
- [ ] Implement `GET /api/admin/dashboard/activity` - Recent activity feed
- [ ] Add superuser guard
- [ ] Write integration tests

**Files to create:**
- `src/py/app/domain/admin/controllers/_dashboard.py`
- `src/py/app/domain/admin/controllers/__init__.py`

### 3.5 Admin Users Controller
- [ ] Create `AdminUsersController` at `/api/admin/users`
- [ ] Implement `GET /api/admin/users` - List with pagination/filtering
- [ ] Implement `GET /api/admin/users/{id}` - User detail
- [ ] Implement `PATCH /api/admin/users/{id}` - Update user
- [ ] Implement `DELETE /api/admin/users/{id}` - Deactivate user
- [ ] Implement `POST /api/admin/users/{id}/verify` - Force verify
- [ ] Add audit logging for all actions
- [ ] Write integration tests

**Files to create:**
- `src/py/app/domain/admin/controllers/_users.py`

### 3.6 Admin Teams Controller
- [ ] Create `AdminTeamsController` at `/api/admin/teams`
- [ ] Implement `GET /api/admin/teams` - List with pagination
- [ ] Implement `GET /api/admin/teams/{id}` - Team detail
- [ ] Implement `PATCH /api/admin/teams/{id}` - Update team
- [ ] Implement `DELETE /api/admin/teams/{id}` - Delete team
- [ ] Add audit logging for all actions
- [ ] Write integration tests

**Files to create:**
- `src/py/app/domain/admin/controllers/_teams.py`

### 3.7 Admin Audit Controller
- [ ] Create `AuditController` at `/api/admin/audit`
- [ ] Implement `GET /api/admin/audit` - List with filtering
- [ ] Implement filtering by actor, action, target, date range
- [ ] Write integration tests

**Files to create:**
- `src/py/app/domain/admin/controllers/_audit.py`

### 3.8 Register Admin Routes
- [ ] Create admin router with all controllers
- [ ] Add to application route handlers
- [ ] Configure superuser-only access

**Files to modify:**
- `src/py/app/server/routes/__init__.py`

### 3.9 Frontend Admin Components
- [ ] Create `stats-cards.tsx` - Dashboard statistics
- [ ] Create `recent-activity.tsx` - Activity feed component
- [ ] Create `user-table.tsx` - User management DataTable
- [ ] Create `team-table.tsx` - Team management DataTable
- [ ] Create `audit-log-table.tsx` - Filterable audit log

**Files to create:**
- `src/js/web/src/components/admin/stats-cards.tsx`
- `src/js/web/src/components/admin/recent-activity.tsx`
- `src/js/web/src/components/admin/user-table.tsx`
- `src/js/web/src/components/admin/team-table.tsx`
- `src/js/web/src/components/admin/audit-log-table.tsx`

### 3.10 Frontend Admin Pages
- [ ] Create admin route group `_app/admin/`
- [ ] Create `admin/index.tsx` - Dashboard
- [ ] Create `admin/users/index.tsx` - User list
- [ ] Create `admin/users/$userId.tsx` - User detail
- [ ] Create `admin/teams/index.tsx` - Team list
- [ ] Create `admin/teams/$teamId.tsx` - Team detail
- [ ] Create `admin/audit.tsx` - Audit log
- [ ] Add admin navigation
- [ ] Create TanStack Query hooks for admin API

**Files to create:**
- `src/js/web/src/routes/_app/admin/index.tsx`
- `src/js/web/src/routes/_app/admin/users/index.tsx`
- `src/js/web/src/routes/_app/admin/users/$userId.tsx`
- `src/js/web/src/routes/_app/admin/teams/index.tsx`
- `src/js/web/src/routes/_app/admin/teams/$teamId.tsx`
- `src/js/web/src/routes/_app/admin/audit.tsx`
- `src/js/web/src/lib/api/hooks/admin.ts`

---

## Phase 4: OAuth Enhancements

### 4.1 OAuth Profile Schemas
- [ ] Create `OAuthAccountInfo` schema
- [ ] Create `OAuthAccountList` schema
- [ ] Update existing OAuth schemas if needed

**Files to modify:**
- `src/py/app/domain/accounts/schemas/_oauth.py`

### 4.2 OAuth Profile Controller
- [ ] Create `OAuthAccountController` at `/api/profile/oauth`
- [ ] Implement `GET /api/profile/oauth/accounts` - List linked accounts
- [ ] Implement `POST /api/profile/oauth/{provider}/link` - Start linking
- [ ] Implement `GET /api/profile/oauth/{provider}/complete` - Complete linking
- [ ] Implement `DELETE /api/profile/oauth/{provider}` - Unlink account
- [ ] Implement `POST /api/profile/oauth/{provider}/upgrade-scopes` - Request permissions
- [ ] Add validation to prevent unlinking only auth method
- [ ] Write integration tests

**Files to create:**
- `src/py/app/domain/accounts/controllers/_oauth_accounts.py`

**Files to modify:**
- `src/py/app/domain/accounts/controllers/__init__.py`

### 4.3 OAuth Token Refresh Job
- [ ] Create background job for OAuth token refresh
- [ ] Implement token refresh logic per provider
- [ ] Handle refresh failures gracefully
- [ ] Add to SAQ job configuration

**Files to create:**
- `src/py/app/domain/accounts/jobs/_oauth_refresh.py`

**Files to modify:**
- `src/py/app/lib/worker.py`

### 4.4 Frontend Connected Accounts
- [ ] Create `connected-accounts.tsx` - OAuth accounts list
- [ ] Create `oauth-link-button.tsx` - Provider link buttons
- [ ] Add connected accounts section to profile
- [ ] Create TanStack Query hooks for OAuth account management

**Files to create:**
- `src/js/web/src/components/profile/connected-accounts.tsx`
- `src/js/web/src/components/profile/oauth-link-button.tsx`

**Files to modify:**
- `src/js/web/src/routes/_app/profile/index.tsx`
- `src/js/web/src/lib/api/hooks/auth.ts`

---

## Phase 5: Railway Deployment

### 5.1 Deploy Script
- [ ] Create `tools/deploy/railway/deploy.sh`
- [ ] Implement Railway CLI installation check
- [ ] Implement project creation/linking
- [ ] Implement PostgreSQL database provisioning
- [ ] Implement app service setup with domain
- [ ] Implement environment variable configuration
- [ ] Implement metal builds enablement
- [ ] Implement deployment with health checks
- [ ] Add comprehensive error handling
- [ ] Add colored output and progress indicators

**Files to create:**
- `tools/deploy/railway/deploy.sh`

### 5.2 Environment Setup Script
- [ ] Create `tools/deploy/railway/env-setup.sh`
- [ ] Implement interactive menu system
- [ ] Implement Resend email setup wizard
- [ ] Implement GitHub OAuth configuration
- [ ] Implement Google OAuth configuration
- [ ] Implement load from .env file capability
- [ ] Implement individual variable setting
- [ ] Add validation for required variables

**Files to create:**
- `tools/deploy/railway/env-setup.sh`

### 5.3 Railway Configuration
- [ ] Create `railway.json` configuration
- [ ] Configure Dockerfile.distroless builder
- [ ] Configure Deploy runtime V2 settings
- [ ] Configure health check path and timeout
- [ ] Configure pre-deploy database migrations
- [ ] Configure CPU/memory limits

**Files to create:**
- `railway.json`

### 5.4 Makefile Updates
- [ ] Add `make deploy-railway` target
- [ ] Add `make railway-env` target
- [ ] Add `make railway-logs` target

**Files to modify:**
- `Makefile`

---

## Phase 6: Frontend Integration & Polish

### 6.1 Run `make types`
- [ ] Generate updated TypeScript client from OpenAPI schema
- [ ] Verify all new endpoints are typed correctly

### 6.2 Navigation Updates
- [ ] Add admin link to navigation (superuser only)
- [ ] Add MFA status indicator to profile menu
- [ ] Update mobile navigation

**Files to modify:**
- `src/js/web/src/components/layout/navigation.tsx`
- `src/js/web/src/components/layout/user-menu.tsx`

### 6.3 Error Handling
- [ ] Add toast notifications for MFA operations
- [ ] Add toast notifications for OAuth operations
- [ ] Add toast notifications for admin operations
- [ ] Ensure all error states have proper UI feedback

### 6.4 Loading States
- [ ] Add loading skeletons for admin tables
- [ ] Add loading states for MFA operations
- [ ] Add loading states for OAuth operations

---

## Phase 7: Final Validation

### 7.1 Backend Testing
- [ ] Run `make test` - All tests pass
- [ ] Run `make lint` - No linting errors
- [ ] Verify test coverage meets requirements

### 7.2 Frontend Testing
- [ ] Run `npm run lint` - No linting errors
- [ ] Run `npm run build` - Build succeeds
- [ ] Manual testing of all new features

### 7.3 Integration Testing
- [ ] Test complete MFA setup and login flow
- [ ] Test refresh token rotation
- [ ] Test OAuth account linking/unlinking
- [ ] Test admin CRUD operations
- [ ] Test audit log entries

### 7.4 Security Review
- [ ] Verify CSRF protection on all mutations
- [ ] Verify refresh token security (hashed, rotation, reuse detection)
- [ ] Verify MFA challenge token scoping
- [ ] Verify admin routes require superuser
- [ ] Verify OAuth state validation

### 7.5 Documentation
- [ ] Update API documentation if needed
- [ ] Document new environment variables
- [ ] Document Railway deployment process

### 7.6 Final Checks
- [ ] Run `make check-all`
- [ ] Verify no regressions in existing functionality
- [ ] Remove any debug code or console logs

---

## Estimated Task Counts

| Phase | Task Count |
|-------|------------|
| **Phase 0: Critical Fixes** | **38** |
| Phase 1: Security Foundation | 28 |
| Phase 2: MFA System | 42 |
| Phase 3: Admin Domain | 45 |
| Phase 4: OAuth Enhancements | 18 |
| Phase 5: Railway Deployment | 16 |
| Phase 6: Frontend Polish | 10 |
| Phase 7: Final Validation | 18 |
| **Total** | **215** |

---

## Dependencies

```
Phase 0 (Critical) ──► Phase 1 (Security) ─┬─► Phase 2 (MFA) ────────────────┐
                                           │                                  │
                                           └─► Phase 3 (Admin) ──────────────┤
                                                                              │
                                           ┌─► Phase 4 (OAuth) ──────────────┼─► Phase 6 ─► Phase 7
                                           │                                  │
                      Phase 5 (Railway) ───┴──────────────────────────────────┘
```

**Phase 0 MUST complete first** - Schema naming and pattern fixes affect all subsequent phases.
Phase 1 must complete before Phase 2 and 3 can start (token infrastructure needed).
Phase 5 (Railway) can proceed in parallel with Phases 1-4.
Phase 6 and 7 require all other phases complete.
