---
description: Quality gate enforcement and pattern extraction
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, mcp__pal__analyze
---

# Review Workflow

Reviewing feature: **$ARGUMENTS**

## Pre-Review Verification

1. Verify implementation is complete
2. Verify all tests pass
3. Load PRD from `specs/active/{slug}/prd.md`
4. Load task list from `specs/active/{slug}/tasks.md`

---

## Review Protocol

### Step 1: Verify All Tasks Complete

Check `specs/active/{slug}/tasks.md`:
- All tasks should be marked complete
- If any incomplete, return to `/implement {slug}`

### Step 2: Quality Gate Verification

Run all quality checks:

```bash
# Run comprehensive checks
make check-all

# Verify tests pass
make test

# Verify linting passes
make lint

# Verify types generated (if schema changes)
make types
```

**All checks must pass before proceeding.**

### Step 3: Code Review Checklist

#### Pattern Compliance

- [ ] Services use inner Repo pattern
- [ ] Schemas use CamelizedBaseStruct (not Pydantic or dicts)
- [ ] Models use UUIDAuditBase and Mapped[] typing
- [ ] Controllers use dependency injection
- [ ] All async operations handled correctly

#### Code Quality

- [ ] No raw dicts in API responses
- [ ] Type hints on all function signatures
- [ ] Docstrings on public methods
- [ ] Error handling follows project patterns
- [ ] No security vulnerabilities (SQL injection, XSS, etc.)

#### Testing

- [ ] 90%+ coverage for modified modules
- [ ] Unit tests for all services
- [ ] Integration tests for API endpoints
- [ ] Edge cases covered

#### Frontend (if applicable)

- [ ] TypeScript types generated (`make types`)
- [ ] Components follow project patterns
- [ ] TanStack Query hooks used correctly
- [ ] TanStack Router routes configured

### Step 4: Pattern Extraction

Check for new patterns in `specs/active/{slug}/tmp/new-patterns.md`.

If new patterns exist, extract to `specs/guides/patterns/`:

```bash
# Example: Extract new validation pattern
cat >> specs/guides/patterns/validation.md << 'EOF'
## {Pattern Name}

### Description
{Description from tmp/new-patterns.md}

### Example
{Code example}

### When to Use
{Use cases}
EOF
```

### Step 5: Documentation Check

Verify documentation is complete:

- [ ] PRD accurately reflects implementation
- [ ] Recovery guide is updated
- [ ] Any pattern deviations documented

### Step 6: Anti-Pattern Scan

Scan for anti-patterns:

```bash
# Check for Optional[] (should use T | None)
grep -r "Optional\[" src/py/app/domain/{domain}/ || echo "✓ No Optional[] found"

# Check for class-based tests (should use functions)
grep -r "class Test" src/py/tests/ | grep -v "__pycache__" || echo "✓ No class-based tests"

# Check for raw dict returns
grep -r "-> dict" src/py/app/domain/{domain}/ || echo "✓ No raw dict returns"

# Check for Pydantic in new code
grep -r "from pydantic import" src/py/app/domain/{domain}/ | grep -v BaseModel || echo "✓ No Pydantic models"
```

### Step 7: Security Review

Check for common security issues:

- [ ] No hardcoded secrets
- [ ] SQL queries use parameterization
- [ ] Input validation on all user data
- [ ] Proper authentication/authorization checks
- [ ] No sensitive data in logs

### Step 8: Performance Review

Consider performance implications:

- [ ] N+1 query prevention (use selectin loading)
- [ ] Appropriate database indexes
- [ ] No unnecessary database calls
- [ ] Pagination for list endpoints

---

## Final Verification

Run final checks:

```bash
# Full test suite
make test

# Full lint check
make lint

# Full type check
make check-all
```

---

## Review Summary

Create review summary in `specs/active/{slug}/review.md`:

```markdown
# Review Summary for {Feature}

## Quality Gates
- [x] Tests pass
- [x] Linting passes
- [x] Type checking passes
- [x] 90%+ coverage

## Pattern Compliance
- [x] Service pattern followed
- [x] Schema pattern followed
- [x] Model pattern followed
- [x] Controller pattern followed

## New Patterns Extracted
- {List of patterns extracted to specs/guides/patterns/}

## Issues Found
- {List of issues, or "None"}

## Approval Status
- [x] Approved for merge
```

---

## Archive Feature Spec

After review approval, archive the feature spec:

```bash
mv specs/active/{slug} specs/archive/{slug}-$(date +%Y%m%d)
```

---

## Completion

```
Review Complete ✓

Feature: {slug}
Status: Approved / Needs Work

Quality Gates:
- ✓ Tests pass
- ✓ Linting passes
- ✓ Type checking passes
- ✓ Coverage: {percentage}%

Patterns Extracted: {count}
Issues Found: {count}

{If approved}: Ready for commit
{If needs work}: Return to /implement {slug}
```
