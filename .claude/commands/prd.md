---
description: Create a PRD with pattern learning and adaptive complexity
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs, mcp__sequential-thinking__sequentialthinking, mcp__pal__planner
---

# Intelligent PRD Creation Workflow

You are creating a Product Requirements Document for: **$ARGUMENTS**

## Intelligence Layer (ACTIVATE FIRST)

Before starting checkpoints:

1. **Read MCP Strategy**: Load `.claude/mcp-strategy.md` for tool selection
2. **Learn from Codebase**: Read 3-5 similar implementations
3. **Assess Complexity**: Determine simple/medium/complex
4. **Adapt Workflow**: Simple=6, Medium=8, Complex=10+ checkpoints

## Critical Rules

1. **CONTEXT FIRST** - Read existing patterns before planning
2. **NO CODE MODIFICATION** - Planning only, no source code changes
3. **PATTERN LEARNING** - Identify 3-5 similar features in codebase
4. **ADAPTIVE DEPTH** - Adjust checkpoints based on complexity
5. **RESEARCH GROUNDED** - Minimum 2000+ words research
6. **COMPREHENSIVE PRD** - Minimum 3200+ words

---

## Checkpoint 0: Intelligence Bootstrap

**Load project intelligence:**

1. Read `CLAUDE.md` for project conventions
2. Read `specs/guides/patterns/README.md` for patterns
3. Read `.claude/mcp-strategy.md` for tool selection

**Learn from existing implementations:**

Search for similar features in `src/py/app/domain/` and `src/js/src/`:
- Find related services, schemas, controllers
- Read at least 3 example implementations
- Extract patterns for reuse

**Assess complexity:**

- **Simple**: Single file CRUD, config change → 6 checkpoints
- **Medium**: New service, API endpoint, 2-3 files → 8 checkpoints
- **Complex**: Architecture change, 5+ files, multi-component → 10+ checkpoints

**Output**: "✓ Checkpoint 0 complete - Complexity: [level], Checkpoints: [count]"

---

## Checkpoint 1: Pattern Recognition

**Identify similar implementations:**

1. Search `src/py/app/domain/` for related domains
2. Read at least 3 service files to understand patterns
3. Check `src/py/app/domain/accounts/` as reference implementation
4. Note naming conventions, class structure, error handling

**Document in workspace:**

```markdown
## Similar Implementations Found

1. `src/py/app/domain/accounts/services/_user.py` - User service pattern
2. `src/py/app/domain/accounts/schemas.py` - Schema pattern
3. `src/py/app/domain/accounts/controllers/` - Controller patterns

## Patterns to Follow

- Service: Inner Repo pattern with SQLAlchemyAsyncRepositoryService
- Schema: CamelizedBaseStruct from msgspec
- Model: UUIDAuditBase with Mapped[] typing
- Controller: Litestar Controller with dependency injection
```

**Output**: "✓ Checkpoint 1 complete - Patterns identified from [N] files"

---

## Checkpoint 2: Workspace Creation

Create the feature workspace:

```bash
mkdir -p specs/active/{slug}/research
mkdir -p specs/active/{slug}/tmp
mkdir -p specs/active/{slug}/patterns
```

**Output**: "✓ Checkpoint 2 complete - Workspace at specs/active/{slug}/"

---

## Checkpoint 3: Intelligent Analysis

**Use appropriate tool based on complexity:**

- **Simple**: Manual structured analysis (document 10 key points)
- **Medium**: Use `mcp__sequential-thinking__sequentialthinking` (15 thoughts)
- **Complex**: Use `mcp__pal__planner` for multi-phase planning

**Document analysis in** `specs/active/{slug}/research/analysis.md`

**Output**: "✓ Checkpoint 3 complete - Analysis using [tool]"

---

## Checkpoint 4: Research (2000+ words)

**Research order of priority:**

1. **Pattern Library**: Check `specs/guides/patterns/` first
2. **Existing Code**: Study similar implementations in codebase
3. **Internal Guides**: Read `CLAUDE.md` thoroughly
4. **Context7**: Look up Litestar, Advanced Alchemy documentation
5. **WebSearch**: Search for best practices if needed

**Write research to** `specs/active/{slug}/research/plan.md`

**Verify word count:**
```bash
wc -w specs/active/{slug}/research/plan.md
```

Must be 2000+ words.

**Output**: "✓ Checkpoint 4 complete - Research ([word count] words)"

---

## Checkpoint 5: Write PRD (3200+ words)

Write comprehensive PRD to `specs/active/{slug}/prd.md`:

**Required sections:**

1. **Intelligence Context**
   - Complexity assessment
   - Similar features referenced
   - Patterns to follow

2. **Problem Statement**
   - User problem being solved
   - Business value
   - Success criteria

3. **Acceptance Criteria**
   - Specific, measurable criteria
   - Edge cases handled
   - Error scenarios

4. **Technical Approach**
   - Pattern references from codebase
   - File structure plan
   - Database changes (if any)
   - API endpoints (if any)
   - Frontend changes (if any)

5. **Testing Strategy**
   - Unit tests (90%+ coverage)
   - Integration tests
   - E2E tests (if applicable)

6. **Implementation Notes**
   - Pattern deviations (with rationale)
   - Dependencies
   - Migration considerations

**Verify word count:**
```bash
wc -w specs/active/{slug}/prd.md
```

Must be 3200+ words.

**Output**: "✓ Checkpoint 5 complete - PRD ([word count] words)"

---

## Checkpoint 6: Task Breakdown

Create task list in `specs/active/{slug}/tasks.md`:

**Adapt tasks to complexity:**

- **Simple (6 tasks)**: Model, Schema, Service, Controller, Test, Frontend
- **Medium (8-10 tasks)**: Add migrations, validations, error handling, integration tests
- **Complex (12+ tasks)**: Add architecture setup, multiple services, frontend state, E2E tests

**Task format:**
```markdown
## Tasks

### Phase 1: Backend Core
- [ ] 1. Create/update model in `db/models/`
- [ ] 2. Run migrations `app database make-migrations`
- [ ] 3. Create msgspec schemas in domain schemas

### Phase 2: Backend Logic
- [ ] 4. Implement service with inner Repo pattern
- [ ] 5. Add controller routes

### Phase 3: Testing
- [ ] 6. Write unit tests (90%+ coverage)
- [ ] 7. Write integration tests

### Phase 4: Frontend
- [ ] 8. Run `make types` to generate TypeScript client
- [ ] 9. Create React components
- [ ] 10. Add TanStack Router routes

### Phase 5: Validation
- [ ] 11. Run `make check-all`
```

**Output**: "✓ Checkpoint 6 complete - [N] tasks created"

---

## Checkpoint 7: Recovery Guide

Create `specs/active/{slug}/recovery.md`:

```markdown
# Recovery Guide for {Feature Name}

## Quick Resume

Last checkpoint: [checkpoint number]
Current phase: [phase name]
Files modified: [list of files]

## Intelligence Context

Complexity: [simple/medium/complex]
Similar implementations:
- [file paths referenced]

Patterns being followed:
- [pattern names]

## State Summary

### Completed
- [list of completed items]

### In Progress
- [current work item]

### Pending
- [remaining items]

## Files to Review

### Models
- [model files]

### Services
- [service files]

### Controllers
- [controller files]

### Tests
- [test files]

## Commands to Run

```bash
# Resume development
cd /home/cody/code/litestar/litestar-fullstack-spa

# Check current state
make check-all

# Run tests
make test
```

## Notes

[Any important context for resuming work]
```

**Output**: "✓ Checkpoint 7 complete - Recovery guide created"

---

## Checkpoint 8: Git Verification

Verify no source code was modified:

```bash
git status --porcelain src/
```

If any source files appear, this is a violation - PRD phase must not modify source code.

**Output**: "✓ Checkpoint 8 complete - No source code modified"

---

## Final Summary

```
PRD Phase Complete ✓

Workspace: specs/active/{slug}/
Complexity: [simple|medium|complex]
Checkpoints: [N] completed

Intelligence:
- ✓ Pattern library consulted
- ✓ [N] similar features analyzed
- ✓ Tool selection optimized

Documents Created:
- prd.md ([word count] words)
- research/plan.md ([word count] words)
- research/analysis.md
- tasks.md ([N] tasks)
- recovery.md

Next: Run `/implement {slug}`
```
