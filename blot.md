# BLOT.md - Comprehensive Task List for Litestar Fullstack SPA

This document provides a comprehensive implementation plan to complete the Litestar Fullstack SPA into a production-ready SaaS boilerplate. Tasks are organized by priority and include implementation guidance.

## Executive Summary

**Current State**:

- ✅ Core authentication working (JWT, teams, RBAC)
- ⚠️ OAuth backend 90% complete, frontend 0%
- ⚠️ Email verification & password reset backend complete, frontend partial
- ❌ 2FA/TOTP backend complete, frontend missing
- ❌ Test coverage insufficient (~60% backend, 0% frontend)
- ❌ Production validation incomplete

**Target State**: Production-ready SaaS boilerplate with complete authentication, testing, and documentation

---

## 🔴 CRITICAL - Phase 1: Complete Authentication System

### 1.1 OAuth Google Integration (Frontend) - HIGH PRIORITY

**Status**: Backend 90% complete, Frontend 0%
**Effort**: 2-3 days

#### Implementation Steps

```typescript
// 1. Create GoogleSignInButton component
// src/js/src/components/auth/google-signin-button.tsx
export function GoogleSignInButton({ variant = 'signin' }: Props) {
  const { mutate: initiateOAuth } = useMutation({
    mutationFn: () => client.auth.googleAuthorize(),
    onSuccess: (data) => {
      window.location.href = data.authorization_url;
    }
  });
  
  return (
    <Button onClick={() => initiateOAuth()} className="w-full">
      <Icons.google className="mr-2 h-4 w-4" />
      Continue with Google
    </Button>
  );
}

// 2. Create callback handler page
// src/js/src/routes/_public/auth/google/callback.tsx
export function GoogleCallbackPage() {
  const searchParams = useSearchParams();
  const code = searchParams.get('code');
  const state = searchParams.get('state');
  
  // Handle OAuth callback
  // Show loading state
  // Handle errors
  // Redirect on success
}

// 3. Update login/signup forms to include OAuth button
// 4. Add OAuth account management in settings
```

#### Tasks

- [ ] Create GoogleSignInButton component with proper Google branding
- [ ] Implement OAuth callback page at `/auth/google/callback`
- [ ] Add OAuth buttons to login/signup forms with divider
- [ ] Create OAuth account linking UI in profile settings
- [ ] Handle OAuth error states (account exists, linking failed)
- [ ] Test complete OAuth flow end-to-end
- [ ] Add loading states and error boundaries

### 1.2 Email Verification Flow (Frontend) - HIGH PRIORITY

**Status**: Backend complete, Frontend partial
**Effort**: 1-2 days

#### Implementation

```typescript
// 1. Email verification banner component
export function EmailVerificationBanner() {
  const { user } = useAuth();
  const [isResending, setIsResending] = useState(false);
  
  if (user?.email_verified_at) return null;
  
  return (
    <Alert className="mb-4">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Verify your email</AlertTitle>
      <AlertDescription>
        Please check your email and click the verification link.
        <Button 
          variant="link" 
          onClick={handleResend}
          disabled={isResending}
        >
          Resend verification email
        </Button>
      </AlertDescription>
    </Alert>
  );
}

// 2. Verification success page
// src/js/src/routes/_public/verify-email.tsx
```

#### Tasks

- [ ] Create email verification banner component
- [ ] Add verification success/error pages
- [ ] Implement resend verification functionality
- [ ] Update signup flow to show verification notice
- [ ] Add email verification status to user profile
- [ ] Handle verification link clicks from email
- [ ] Test email verification end-to-end

### 1.3 Password Reset Flow (Frontend) - HIGH PRIORITY

**Status**: Backend complete, Frontend missing
**Effort**: 1 day

#### Implementation

```typescript
// 1. Forgot password form
// src/js/src/routes/_public/forgot-password.tsx
export function ForgotPasswordPage() {
  const form = useForm<{ email: string }>({
    resolver: zodResolver(forgotPasswordSchema),
  });
  
  const { mutate: requestReset } = useMutation({
    mutationFn: (data) => client.access.forgotPassword(data),
    onSuccess: () => {
      toast.success("Check your email for reset instructions");
    }
  });
  
  return (
    <Form {...form}>
      {/* Email input field */}
      {/* Submit button */}
      {/* Success message */}
    </Form>
  );
}

// 2. Reset password form with token validation
// src/js/src/routes/_public/reset-password.tsx
```

#### Tasks

- [ ] Create forgot password page with email form
- [ ] Create reset password page with token validation
- [ ] Add "Forgot Password?" link to login form
- [ ] Implement password strength indicator
- [ ] Handle reset token expiration
- [ ] Add success redirect to login
- [ ] Test complete password reset flow

### 1.4 Two-Factor Authentication (Frontend) - MEDIUM PRIORITY

**Status**: Backend complete, Frontend 0%
**Effort**: 2-3 days

#### Implementation

```typescript
// 1. 2FA setup wizard
// src/js/src/components/settings/two-factor-setup.tsx
export function TwoFactorSetup() {
  const [step, setStep] = useState<'init' | 'verify' | 'backup'>('init');
  const [qrCode, setQrCode] = useState<string>();
  const [backupCodes, setBackupCodes] = useState<string[]>();
  
  // Step 1: Show QR code
  // Step 2: Verify TOTP code
  // Step 3: Display backup codes
}

// 2. 2FA verification during login
// src/js/src/components/auth/two-factor-verify.tsx
export function TwoFactorVerify({ tempToken }: Props) {
  const [code, setCode] = useState('');
  
  return (
    <div className="space-y-4">
      <InputOTP value={code} onChange={setCode} maxLength={6}>
        <InputOTPGroup>
          <InputOTPSlot index={0} />
          {/* ... more slots */}
        </InputOTPGroup>
      </InputOTP>
      <Button onClick={handleVerify}>Verify</Button>
      <Button variant="link">Use backup code</Button>
    </div>
  );
}
```

#### Tasks

- [ ] Create 2FA setup wizard with QR code display
- [ ] Implement TOTP input component for verification
- [ ] Add 2FA step to login flow
- [ ] Create backup codes display/download component
- [ ] Add 2FA management in security settings
- [ ] Implement device trust/remember feature
- [ ] Test 2FA setup and login flows

---

## 🟠 HIGH - Phase 2: Complete Testing Framework

### 2.1 Backend Testing Overhaul - CRITICAL

**Status**: ~60% coverage, many outdated tests
**Effort**: 5-7 days

#### Priority Test Areas

```python
# 1. Service layer tests (HIGH PRIORITY)
# src/py/tests/unit/services/test_user_service.py
@pytest.mark.unit
async def test_user_authentication_flow():
    """Test complete authentication flow including 2FA"""
    # Test password authentication
    # Test email verification requirement
    # Test 2FA requirement check
    # Test token generation

# 2. Integration tests for new features
# src/py/tests/integration/test_email_verification.py
@pytest.mark.integration
async def test_email_verification_flow():
    """Test complete email verification flow"""
    # Create unverified user
    # Send verification email
    # Verify token
    # Check user status update

# 3. OAuth flow tests
# src/py/tests/integration/test_oauth.py
@pytest.mark.integration
async def test_google_oauth_flow():
    """Test Google OAuth with mocked responses"""
    # Mock Google OAuth responses
    # Test authorization URL generation
    # Test callback handling
    # Test user creation/linking
```

#### Tasks

- [ ] Fix all existing broken tests (update to current codebase)
- [ ] Add UserService authentication tests with 2FA
- [ ] Add email verification service tests
- [ ] Add password reset service tests
- [ ] Add OAuth service tests with mocking
- [ ] Add TeamService comprehensive tests
- [ ] Add integration tests for all API endpoints
- [ ] Add validation tests for msgspec schemas
- [ ] Add security tests (SQL injection, XSS, CSRF)
- [ ] Achieve 90%+ coverage for critical paths

### 2.2 Frontend Testing Setup - HIGH

**Status**: 0% coverage
**Effort**: 3-5 days

#### Setup Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/lib/api/'],
    },
  },
});

// src/test/setup.ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

#### Priority Tests

```typescript
// 1. Authentication components
// src/js/src/components/auth/__tests__/login.test.tsx
describe('LoginForm', () => {
  it('validates email format', async () => {});
  it('validates password requirements', async () => {});
  it('handles login success', async () => {});
  it('handles login failure', async () => {});
  it('shows 2FA input when required', async () => {});
});

// 2. Critical user flows
// src/js/src/routes/__tests__/signup-flow.test.tsx
describe('Signup Flow', () => {
  it('completes signup with email verification', async () => {});
  it('handles OAuth signup', async () => {});
  it('validates all form fields', async () => {});
});
```

#### Tasks

- [ ] Setup Vitest + React Testing Library
- [ ] Setup MSW for API mocking
- [ ] Add component tests for auth forms
- [ ] Add tests for team management components
- [ ] Add tests for user profile components
- [ ] Add integration tests for critical flows
- [ ] Setup E2E with Playwright (optional)
- [ ] Add visual regression tests (optional)

---

## 🟡 MEDIUM - Phase 3: UI/UX Improvements

### 3.1 Error Handling & Loading States - HIGH

**Effort**: 2 days

#### Implementation

```typescript
// 1. Global error boundary
// src/js/src/components/error-boundary.tsx
export function ErrorBoundary({ children }: Props) {
  return (
    <ReactErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={() => window.location.href = '/'}
    >
      {children}
    </ReactErrorBoundary>
  );
}

// 2. Consistent loading states
// src/js/src/components/ui/loading.tsx
export function LoadingSpinner({ size = 'default' }: Props) {
  return (
    <div className="flex items-center justify-center p-4">
      <Loader2 className={cn('animate-spin', sizeClasses[size])} />
    </div>
  );
}

// 3. Empty states for all lists
// src/js/src/components/ui/empty-state.tsx
export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action 
}: Props) {
  return (
    <div className="text-center py-12">
      <Icon className="mx-auto h-12 w-12 text-muted-foreground" />
      <h3 className="mt-2 text-sm font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
```

#### Tasks

- [ ] Implement global error boundary with fallback UI
- [ ] Add loading skeletons for all data-fetching components
- [ ] Create empty state components for lists/tables
- [ ] Improve toast notifications (success/error/warning)
- [ ] Add offline state detection and handling
- [ ] Implement optimistic updates where appropriate
- [ ] Add proper 404/500 error pages
- [ ] Ensure all forms show validation errors clearly

### 3.2 Admin Dashboard - MEDIUM

**Status**: Basic implementation exists
**Effort**: 3-4 days

#### Enhanced Admin Features

```typescript
// 1. Admin dashboard with analytics
// src/js/src/routes/_app/admin/dashboard.tsx
export function AdminDashboard() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <StatsCard title="Total Users" value={stats.totalUsers} />
      <StatsCard title="Active Teams" value={stats.activeTeams} />
      <StatsCard title="Daily Signups" value={stats.dailySignups} />
      <StatsCard title="System Health" value="Operational" />
      
      <UserGrowthChart />
      <TeamActivityChart />
      <RecentUsersTable />
      <SystemLogsViewer />
    </div>
  );
}

// 2. User management with bulk actions
// src/js/src/routes/_app/admin/users.tsx
```

#### Tasks

- [ ] Create admin dashboard with key metrics
- [ ] Add user management with search/filter/sort
- [ ] Implement bulk user actions (activate/deactivate/delete)
- [ ] Add team oversight and management
- [ ] Create role/permission management UI
- [ ] Add system configuration interface
- [ ] Implement audit log viewer
- [ ] Add user impersonation feature (with logging)

### 3.3 User Profile Enhancement - MEDIUM

**Effort**: 2 days

#### Tasks

- [ ] Add avatar upload with crop/resize
- [ ] Create comprehensive profile settings page
- [ ] Add account preferences (notifications, privacy)
- [ ] Implement email change with verification
- [ ] Add timezone and locale settings
- [ ] Create activity/session history view
- [ ] Add account export/deletion options

---

## 🟢 LOWER - Phase 4: Documentation & DevOps

### 4.1 Documentation Overhaul - MEDIUM

**Effort**: 2-3 days

#### Priority Documentation

```markdown
# 1. Getting Started Guide
docs/getting-started.md
- Prerequisites
- Installation steps
- First-time setup
- Common issues

# 2. API Documentation
docs/api/
- Authentication flows
- Endpoint reference
- Request/response examples
- Error codes

# 3. Deployment Guide
docs/deployment.md
- Docker deployment
- Kubernetes setup
- Environment variables
- Security checklist

# 4. Development Guide
docs/development.md
- Architecture overview
- Adding new features
- Testing guidelines
- Code style guide
```

#### Tasks

- [ ] Update README with complete setup instructions
- [ ] Create getting started guide with screenshots
- [ ] Document all API endpoints with examples
- [ ] Create deployment guide for production
- [ ] Add architecture decision records (ADRs)
- [ ] Document configuration options
- [ ] Create troubleshooting guide
- [ ] Add video tutorials for common workflows

### 4.2 CI/CD Pipeline - MEDIUM

**Effort**: 2 days

#### GitHub Actions Setup

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
      - name: Install dependencies
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv sync --dev
      - name: Run tests
        run: |
          uv run pytest --cov=src/py/app --cov-fail-under=90
      
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
      - name: Install dependencies
        run: cd src/js && npm ci
      - name: Run tests
        run: cd src/js && npm test
      - name: Build
        run: cd src/js && npm run build
```

#### Tasks

- [ ] Setup GitHub Actions for backend testing
- [ ] Setup GitHub Actions for frontend testing
- [ ] Add security scanning (Snyk/Dependabot)
- [ ] Configure automated dependency updates
- [ ] Add Docker image building and pushing
- [ ] Setup staging deployment pipeline
- [ ] Add performance testing in CI
- [ ] Configure code coverage reporting

### 4.3 Production Readiness - LOW

**Effort**: 3-4 days

#### Tasks

- [ ] Add comprehensive health check endpoints
- [ ] Implement structured logging with correlation IDs
- [ ] Setup Sentry error tracking integration
- [ ] Add APM monitoring (DataDog/New Relic)
- [ ] Configure rate limiting for all endpoints
- [ ] Implement CSRF protection
- [ ] Add security headers middleware
- [ ] Setup database connection pooling optimization
- [ ] Create database backup strategy
- [ ] Document disaster recovery procedures

---

## 📋 Quick Wins (Can Start Immediately)

### Code Quality Fixes - 1 day

- [ ] Fix all TODO comments in codebase (14 found)
- [ ] Remove console.error debug statements
- [ ] Fix TypeScript type generation issues
- [ ] Update all dependencies to latest versions
- [ ] Run `make check-all` and fix all issues
- [ ] Remove dead code and unused imports
- [ ] Add missing type annotations

### UI Polish - 1 day

- [ ] Fix form validation error display
- [ ] Improve loading spinner consistency
- [ ] Add keyboard navigation support
- [ ] Fix accessibility issues (ARIA labels, focus management)
- [ ] Ensure mobile responsiveness
- [ ] Add proper meta tags for SEO
- [ ] Implement dark mode toggle persistence

### Backend Improvements - 1 day

- [ ] Add comprehensive input validation to all endpoints
- [ ] Improve error messages for better UX
- [ ] Add request/response logging with correlation IDs
- [ ] Implement database query optimization
- [ ] Add missing database indexes
- [ ] Setup Redis caching for frequently accessed data

---

## 🎯 Implementation Priority Order

### Week 1: Critical Authentication

1. OAuth Frontend Implementation (2-3 days)
2. Email Verification Frontend (1-2 days)
3. Password Reset Frontend (1 day)
4. Quick Wins - Code Quality (1 day)

### Week 2: Testing Foundation

1. Fix existing backend tests (2 days)
2. Add critical service tests (2 days)
3. Setup frontend testing (1 day)

### Week 3: UI/UX & Testing

1. Error handling & loading states (2 days)
2. 2FA Frontend implementation (2 days)
3. Frontend component tests (1 day)

### Week 4: Admin & Documentation

1. Admin dashboard enhancement (2 days)
2. Documentation overhaul (2 days)
3. CI/CD pipeline setup (1 day)

### Week 5: Polish & Production

1. User profile enhancements (2 days)
2. Integration testing (2 days)
3. Production readiness tasks (1 day)

---

## 📊 Success Metrics

### MVP Completion (2 weeks)

- [ ] All authentication flows working (OAuth, email verification, password reset)
- [ ] 80%+ backend test coverage
- [ ] Basic frontend tests in place
- [ ] Error handling implemented
- [ ] Core documentation complete

### Production Ready (4-5 weeks)

- [ ] 90%+ backend test coverage
- [ ] 70%+ frontend test coverage
- [ ] All security features implemented (2FA, rate limiting)
- [ ] Complete admin interface
- [ ] Full documentation suite
- [ ] CI/CD pipeline operational
- [ ] Performance monitoring in place
- [ ] Zero critical bugs

---

## 🚀 Getting Started

1. **Review current state**: Run `make test` to see failing tests
2. **Fix immediate issues**: Start with Quick Wins section
3. **Focus on authentication**: Complete OAuth frontend first
4. **Build test coverage**: Fix tests as you implement features
5. **Document as you go**: Update docs with each feature

## Notes

- **Team coordination**: Frontend and backend tasks can be parallelized
- **Dependencies**: OAuth requires Google Cloud Console setup
- **Testing**: Don't skip tests - they ensure production readiness
- **Security**: All auth features must have security tests
- **Performance**: Add monitoring before going to production

---

Generated: 2025-08-17
Last Updated: 2025-08-17
Version: 1.0.0
