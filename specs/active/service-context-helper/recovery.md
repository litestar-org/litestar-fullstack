# Recovery Guide: Service Context Manager Helper

## Quick Resume

| Field | Value |
|-------|-------|
| **Last checkpoint** | PRD Phase Complete |
| **Current phase** | Ready for Implementation |
| **Files modified** | None (specs only) |
| **Next action** | Run `/implement service-context-helper` |

---

## Intelligence Context

| Dimension | Value |
|-----------|-------|
| **Complexity** | Medium |
| **Checkpoints** | 8 |
| **Risk Level** | Low |

### Similar Implementations Referenced

1. `advanced_alchemy.extensions.litestar.providers.create_service_provider` - Factory pattern
2. `advanced_alchemy.service._async.SQLAlchemyAsyncRepositoryService.new()` - Context manager pattern
3. `src/py/app/domain/system/jobs.py:cleanup_auth_tokens` - Multi-service orchestration
4. `src/py/app/domain/accounts/guards.py:current_user_from_token` - Request-scoped session
5. `src/py/app/cli/commands.py:_create_default_roles` - CLI session management

### Patterns Being Followed

- **Async Context Manager**: `@asynccontextmanager` from `contextlib`
- **Type Overloads**: `@overload` for tuple return typing (1-5 providers)
- **Inner Import**: Import `alchemy` inside function to avoid circular imports
- **Service Provider Reuse**: Use existing `provide_*_service` functions with `anext()`

---

## State Summary

### Completed
- [x] Problem analysis and quantification
- [x] Pattern research and documentation
- [x] API design (tuple unpacking style)
- [x] User preference clarification (session sources, API style, provider reuse)
- [x] Technical specification
- [x] Test strategy definition
- [x] Task breakdown (12 tasks, 4 phases)

### In Progress
- [ ] Implementation not started

### Pending
- [ ] Add `provide_services` to `deps.py`
- [ ] Update 5 files to use new helper
- [ ] Create unit tests
- [ ] Run validation

---

## Files to Modify

### Primary Implementation

| File | Action | Status |
|------|--------|--------|
| `src/py/app/lib/deps.py` | Add helper | Pending |

### Update Sites

| File | Function | Status |
|------|----------|--------|
| `src/py/app/domain/system/jobs.py` | `cleanup_auth_tokens` | Pending |
| `src/py/app/domain/accounts/guards.py` | `current_user_from_token` | Pending |
| `src/py/app/domain/accounts/signals.py` | `user_created_event_handler` | Pending |
| `src/py/app/domain/teams/signals.py` | `team_created_event_handler` | Pending |
| `src/py/app/cli/commands.py` | `_create_user`, `_create_default_roles` | Pending |

### New Files

| File | Purpose | Status |
|------|---------|--------|
| `src/py/tests/unit/test_deps.py` | Unit tests | Pending |

---

## Commands to Run

```bash
# Resume development
cd /home/cody/code/litestar/litestar-fullstack-spa

# View current specs
cat specs/active/service-context-helper/prd.md
cat specs/active/service-context-helper/tasks.md

# After implementation - validation
make lint
make test
make check-all
```

---

## Key Design Decisions

### API Style
**Chosen**: Tuple unpacking
```python
async with provide_services(p1, p2) as (s1, s2):
```

**Why**: Most concise, preserves type inference, matches Python patterns

### Session Sources
**Supported**: All three patterns
1. Standalone (auto-session from `alchemy.get_session()`)
2. Request context (`connection` parameter)
3. Explicit (`session` parameter)

**Why**: Each use case in codebase needs different session sources

### Provider Reuse
**Chosen**: Reuse existing provider functions with `anext()`

**Why**: Maintains consistency with Litestar DI patterns, preserves custom configuration

---

## Transformation Examples

### Background Job (3 services)

**Before** (jobs.py:19-22):
```python
async with alchemy.get_session() as db_session:
    verification_service = await anext(account_deps.provide_email_verification_service(db_session))
    reset_service = await anext(account_deps.provide_password_reset_service(db_session))
    refresh_service = await anext(account_deps.provide_refresh_token_service(db_session))
```

**After**:
```python
async with provide_services(
    account_deps.provide_email_verification_service,
    account_deps.provide_password_reset_service,
    account_deps.provide_refresh_token_service,
) as (verification_service, reset_service, refresh_service):
```

### Auth Guard (connection pattern)

**Before** (guards.py:106-108):
```python
service = await anext(
    deps.provide_users_service(config.alchemy.provide_session(connection.app.state, connection.scope))
)
```

**After**:
```python
async with provide_services(deps.provide_users_service, connection=connection) as (service,):
```

---

## Notes

### Import Considerations
- `alchemy` config must be imported inside `provide_services` to avoid circular imports
- Update sites will need to import `provide_services` from `app.lib.deps`

### Type Safety
- Overloads cover 1-5 providers with proper tuple typing
- Beyond 5 providers, falls back to `tuple[Any, ...]`

### Testing Priority
1. Validation error cases (easy, fast)
2. Standalone session mode (most common use)
3. Connection mode (guards)
4. Explicit session mode (edge case)

---

## Spec Files

| File | Purpose | Word Count |
|------|---------|------------|
| `specs/active/service-context-helper/prd.md` | Full requirements | ~3,500 |
| `specs/active/service-context-helper/research/plan.md` | Research document | ~2,400 |
| `specs/active/service-context-helper/research/analysis.md` | Pattern analysis | ~800 |
| `specs/active/service-context-helper/tasks.md` | Task breakdown | 12 tasks |
| `specs/active/service-context-helper/recovery.md` | This file | - |
