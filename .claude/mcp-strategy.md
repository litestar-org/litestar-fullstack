# MCP Tool Strategy

## Tool Selection by Task Type

### Complex Architectural Decisions

1. **Primary**: `mcp__pal__thinkdeep`
2. **Fallback**: `mcp__sequential-thinking__sequentialthinking`

Use when: Designing new features, refactoring, performance analysis

### Library Documentation Lookup

1. **Primary**: `mcp__context7__resolve-library-id` + `mcp__context7__query-docs`
2. **Fallback**: `WebSearch`

**Common library IDs for this project:**

- Litestar: `/litestar-org/litestar`
- Advanced Alchemy: `/litestar-org/advanced-alchemy`
- SQLAlchemy: `/sqlalchemy/sqlalchemy`
- TanStack Router: `/tanstack/router`
- TanStack Query: `/tanstack/query`
- React: `/facebook/react`
- Tailwind CSS: `/tailwindlabs/tailwindcss`
- msgspec: `/jcrist/msgspec`

### Multi-Phase Planning

1. **Primary**: `mcp__pal__planner`
2. **Fallback**: Manual structured thinking with checkpoints

Use when: Multi-step features, migrations, refactoring

### Code Analysis

1. **Primary**: `mcp__pal__analyze`
2. **Fallback**: Manual code review with grep/glob

Use when: Architecture review, code quality assessment

### Debugging

1. **Primary**: `mcp__pal__debug`
2. **Fallback**: Manual investigation

Use when: Bug investigation, performance issues

### Multi-Model Consensus

1. **Primary**: `mcp__pal__consensus`

Use when: Architecture decisions needing multiple perspectives

## Complexity-Based Tool Selection

### Simple Features (6 checkpoints)

- Use basic tools (Read, Grep, Glob)
- Manual analysis acceptable
- Focus on speed

### Medium Features (8 checkpoints)

- Use `mcp__sequential-thinking__sequentialthinking` (12-15 steps)
- Include pattern analysis phase
- Moderate documentation lookup

### Complex Features (10+ checkpoints)

- Use `mcp__pal__thinkdeep` or `mcp__pal__planner`
- Deep pattern analysis required
- Comprehensive research phase
- Multi-file impact analysis

## Context7 Usage Examples

### Looking up Litestar patterns

```python
# First resolve the library ID
mcp__context7__resolve-library-id(
    libraryName="litestar",
    query="How to create a controller with dependency injection"
)

# Then query the docs
mcp__context7__query-docs(
    libraryId="/litestar-org/litestar",
    query="Controller dependency injection examples"
)
```

### Looking up Advanced Alchemy patterns

```python
mcp__context7__resolve-library-id(
    libraryName="advanced-alchemy",
    query="Service repository pattern async"
)

mcp__context7__query-docs(
    libraryId="/litestar-org/advanced-alchemy",
    query="SQLAlchemyAsyncRepositoryService usage"
)
```

### Looking up TanStack Router

```python
mcp__context7__query-docs(
    libraryId="/tanstack/router",
    query="createFileRoute loader data fetching"
)
```

## PAL Tools Configuration

### ThinkDeep Usage

For architectural analysis requiring deep investigation:

```python
mcp__pal__thinkdeep(
    step="Analyzing authentication flow architecture",
    step_number=1,
    total_steps=3,
    next_step_required=True,
    findings="Initial observations...",
    confidence="medium",
    relevant_files=[
        "/home/cody/code/litestar/litestar-fullstack-spa/src/py/app/domain/accounts/services/_user.py"
    ]
)
```

### Planner Usage

For multi-phase project planning:

```python
mcp__pal__planner(
    step="Phase 1: Define feature requirements and scope",
    step_number=1,
    total_steps=4,
    next_step_required=True
)
```

### Debug Usage

For systematic bug investigation:

```python
mcp__pal__debug(
    step="Investigating authentication failure",
    step_number=1,
    total_steps=3,
    next_step_required=True,
    findings="Error occurs when...",
    hypothesis="JWT token validation failing due to..."
)
```
