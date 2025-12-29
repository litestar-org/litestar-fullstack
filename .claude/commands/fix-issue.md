---
description: Fix a GitHub issue with intelligent debugging
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, WebFetch, mcp__pal__debug, mcp__pal__thinkdeep
---

# GitHub Issue Fix Workflow

Fixing issue: **$ARGUMENTS**

## Step 1: Fetch Issue Details

```bash
# Get issue details (replace # with issue number)
gh issue view {issue_number}

# Get issue comments
gh issue view {issue_number} --comments
```

## Step 2: Understand the Issue

Parse the issue to identify:

1. **Type**: Bug, Feature Request, Enhancement, Documentation
2. **Severity**: Critical, High, Medium, Low
3. **Affected Areas**: Backend, Frontend, Database, API
4. **Reproduction Steps**: How to reproduce (if bug)
5. **Expected Behavior**: What should happen
6. **Actual Behavior**: What currently happens

## Step 3: Assess Complexity

**Simple Issue (1-3 files)**:
- Proceed directly to fix

**Medium Issue (3-5 files)**:
- Create mini-spec in `specs/active/issue-{number}/`
- Plan before implementing

**Complex Issue (5+ files)**:
- Create full PRD with `/prd issue-{number}`
- Follow full workflow

## Step 4: Root Cause Analysis

For bugs, use `mcp__pal__debug`:

```python
mcp__pal__debug(
    step="Investigating issue #{number}: {title}",
    step_number=1,
    total_steps=3,
    next_step_required=True,
    findings="Initial observations...",
    hypothesis="The issue may be caused by...",
    relevant_files=["src/py/app/..."]
)
```

For feature requests, use `mcp__pal__thinkdeep`:

```python
mcp__pal__thinkdeep(
    step="Analyzing requirements for issue #{number}",
    step_number=1,
    total_steps=3,
    next_step_required=True,
    findings="The feature needs...",
    relevant_files=["src/py/app/..."]
)
```

## Step 5: Locate Affected Code

```bash
# Search for keywords from issue
grep -r "{keyword}" src/py/app/ --include="*.py"

# Find related files
find src/ -name "*{related}*" -type f
```

## Step 6: Implement Fix

### For Bugs

1. **Reproduce the issue** first
2. **Write a failing test** that demonstrates the bug
3. **Fix the code** to make the test pass
4. **Verify no regressions** with full test suite

### For Features

1. **Follow existing patterns** from similar features
2. **Write tests** alongside implementation
3. **Update documentation** if needed

## Step 7: Verify Fix

```bash
# Run all tests
make test

# Run linting
make lint

# Run type checks
make check-all

# Run specific tests for affected area
uv run pytest src/py/tests/unit/test_{domain}/ -xvs
```

## Step 8: Create Commit

Follow the commit message format:

```bash
git add .
git commit -m "$(cat <<'EOF'
fix: {short description} (#{issue_number})

{Longer description of the fix}

- {Change 1}
- {Change 2}

Closes #{issue_number}
EOF
)"
```

## Step 9: Update Issue

```bash
# Add comment with fix details
gh issue comment {issue_number} --body "Fixed in commit {sha}.

Changes:
- {Change 1}
- {Change 2}

This will be included in the next release."
```

## Step 10: Create PR (if needed)

```bash
gh pr create --title "fix: {description} (#issue_number)" \
  --body "## Summary
Fixes #{issue_number}

## Changes
- {Change 1}
- {Change 2}

## Test Plan
- [x] Unit tests added/updated
- [x] Integration tests pass
- [x] Manual testing completed"
```

---

## Issue Type Templates

### Bug Fix Template

```markdown
## Issue Analysis
- **Type**: Bug
- **Severity**: {level}
- **Affected**: {components}

## Root Cause
{Description of what's causing the bug}

## Fix Approach
{How you'll fix it}

## Files Modified
- `{file1}` - {change}
- `{file2}` - {change}

## Testing
- [ ] Failing test added
- [ ] Fix implemented
- [ ] Test passes
- [ ] No regressions
```

### Feature Request Template

```markdown
## Issue Analysis
- **Type**: Feature
- **Scope**: {small/medium/large}
- **Components**: {affected areas}

## Approach
{How you'll implement it}

## Files to Create/Modify
- `{file1}` - {change}
- `{file2}` - {change}

## Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Documentation updated
```

---

## Quick Reference

```bash
# View issue
gh issue view {number}

# Add label
gh issue edit {number} --add-label "bug"

# Assign to self
gh issue edit {number} --add-assignee @me

# Close issue
gh issue close {number}

# Link PR to issue
gh pr create --title "fix: ..." --body "Closes #{number}"
```
