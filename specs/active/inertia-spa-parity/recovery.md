# Recovery Guide: Inertia to SPA Parity

This document provides context recovery information for future sessions working on this PRD.

## Quick Start for New Sessions

```
Read these files in order:
1. specs/active/inertia-spa-parity/prd.md - Full requirements (see Section 9 for critical fixes)
2. specs/active/inertia-spa-parity/tasks.md - Task breakdown (Phase 0 = PRIORITY)
3. specs/active/inertia-spa-parity/research/critical-fixes.md - Critical fix details
4. specs/active/inertia-spa-parity/research/plan.md - Technical research
```

## Project Context

**Goal:** Achieve feature parity between `litestar-fullstack-inertia` and `litestar-fullstack-spa` projects.

**Key Difference:** Inertia uses server-side rendering with sessions. SPA uses client-side React with JWT + HTTP-only cookies.

**Complexity:** COMPLEX (10+ phases, 215 tasks)

**JS Directory Structure (Updated 2025-12-29):**
- Web app: `src/js/web/` (moved from `src/js/`)
- Email templates: `src/js/templates/`

## ✅ COMPLETED Phase 0 Tasks

### 0.1 Schema Naming ✅ DONE
All schemas renamed in `src/py/app/domain/accounts/schemas/` and `src/py/app/domain/admin/schemas/`.
TypeScript client regenerated and frontend API client updated for fetch-based hey-api.

### 0.2 Frontend Validation ✅ DONE
Created `src/js/web/src/lib/validation.ts` with Zod schemas for all forms.

### 0.2.5 JS Directory Reorganization ✅ DONE
- Moved web app from `src/js/` to `src/js/web/`
- Created `src/js/templates/` for email templates
- Updated all config files (Makefile, Dockerfiles, pyproject.toml, settings.py, etc.)
- Updated `tools/manage_assets.py` to use bun instead of npm

### 0.3 React Email Templates ✅ DONE
- Created `src/js/templates/` with all components and email templates
- Components: Layout, Header, Footer, Button
- Email templates: email-verification, password-reset, welcome, team-invitation
- Build script: `bun run build` compiles to HTML in `src/py/app/server/static/email/`
- Makefile target: `make build-emails`

### 0.3.5 Build System & Docker Updates ✅ DONE
- Fixed Makefile `build-emails` command (shell context issue)
- Updated all Dockerfiles (Dockerfile, Dockerfile.dev, Dockerfile.distroless) to:
  - Copy email templates package.json and bun.lock
  - Install email template dependencies
  - Build email templates before wheel build
- Added `force-include` to pyproject.toml for wheel packaging:
  - `src/py/app/server/static/web` → `app/server/static/web`
  - `src/py/app/server/static/email` → `app/server/static/email`
- Verified wheel contains 689 files (Python code + assets + email templates)

### 0.4 Verified OK (No Changes)
- ✅ Deferred security groups on User model
- ✅ Advanced Alchemy service hooks
- ✅ Service provider pattern

## Critical Architectural Decisions

### Authentication Architecture (Consensus Result)

**Decision:** Keep JWT with HTTP-only cookies, add refresh token rotation.

**Security Requirements (UNANIMOUS from Gemini 3 Pro + GPT 5.2):**
1. HTTP-only cookies required (never localStorage)
2. CSRF protection mandatory
3. Refresh token rotation with reuse detection
4. Hashed token storage (SHA-256)
5. MFA challenge token with strict scope

### Token Configuration

| Token Type | Expiry | Cookie Settings |
|------------|--------|-----------------|
| Access Token | 15 min | HttpOnly, Secure, SameSite=Lax, Path=/ |
| Refresh Token | 7 days | HttpOnly, Secure, SameSite=Strict, Path=/api/auth/refresh |
| MFA Challenge | 5 min | NOT in cookie - returned in response body |

### MFA Challenge Token Requirements

```
Claims:
- type: "mfa_challenge"
- aud: "mfa_verification"
- amr: ["pwd"]
- exp: 5 minutes
```

## Reference Files from Inertia Project

Key files to reference from `../litestar-fullstack-inertia/`:

```
app/domain/accounts/controllers/_mfa.py          # MFA management
app/domain/accounts/controllers/_mfa_challenge.py # MFA login flow
app/domain/accounts/controllers/_oauth_accounts.py # OAuth profile
app/domain/admin/controllers/_dashboard.py       # Admin dashboard
tools/deploy/railway/deploy.sh                   # Railway deployment
tools/deploy/railway/env-setup.sh                # Environment setup
railway.json                                     # Railway config
```

## Phase Dependencies

```
Phase 0 (Critical Fixes) MUST complete FIRST!
    ↓
Phase 1 (Security Foundation)
    ↓
Phase 2 (MFA) and Phase 3 (Admin) can proceed in parallel
    ↓
Phase 4 (OAuth) depends on security infrastructure
    ↓
Phase 5 (Railway) is independent - can run anytime after Phase 0
    ↓
Phase 6 (Frontend) and Phase 7 (Validation) require all above
```

## Existing Infrastructure to Leverage

### Backend (Already Exists)

- `src/py/app/lib/crypt.py` - TOTP functions (generate_totp_secret, verify_totp_code, etc.)
- `src/py/app/domain/accounts/services/_user_oauth_account.py` - OAuth account service
- `src/py/app/domain/accounts/controllers/_oauth.py` - Stateless OAuth login
- Email templates in Jinja2 format (no changes needed)

### Frontend (Already Exists)

- TanStack Router setup
- TanStack Query configuration
- API client with interceptors
- Authentication context

## Key Patterns to Follow

### Service Pattern (Inner Repository)

```python
from litestar.plugins.sqlalchemy import repository, service
from app.db import models as m

class MyService(service.SQLAlchemyAsyncRepositoryService[m.MyModel]):
    class Repo(repository.SQLAlchemyAsyncRepository[m.MyModel]):
        model_type = m.MyModel
    repository_type = Repo
```

### Schema Pattern (msgspec)

```python
from app.lib.schema import CamelizedBaseStruct

class MySchema(CamelizedBaseStruct, gc=False, array_like=True, omit_defaults=True):
    field: str
```

### Controller Pattern

```python
from litestar import Controller, get, post
from litestar.di import Provide

class MyController(Controller):
    path = "/my-path"
    dependencies = {"service": Provide(provide_service)}
```

## Common Commands

```bash
# After schema changes
make types

# Before committing
make check-all

# Run specific tests
uv run pytest src/py/tests/integration/test_file.py -xvs

# Database migrations
app database make-migrations
app database upgrade
```

## Files Created by This PRD

```
specs/active/inertia-spa-parity/
├── prd.md              # Product Requirements Document (see Section 9 for critical fixes)
├── tasks.md            # Detailed task breakdown (215 tasks, Phase 0 = PRIORITY)
├── recovery.md         # This file
└── research/
    ├── plan.md         # Technical research
    └── critical-fixes.md # Critical fix details (2025-12-29)
```

## Known Considerations

1. **CSRF Exemptions:** OAuth callback routes need CSRF exemption
2. **Rate Limiting:** MFA endpoints need strict rate limiting (5 attempts/15 min)
3. **Audit Logging:** All admin actions must be logged
4. **Background Jobs:** Refresh token cleanup and OAuth token refresh jobs needed
5. **Error Codes:** Use consistent error codes across all endpoints

## Validation Checklist

Before marking any phase complete:

- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Types generated (`make types`)
- [ ] Integration tests added
- [ ] No security vulnerabilities introduced
- [ ] Audit logging for sensitive operations
