# Litestar-Vite Skill

Quick reference for litestar-vite integration in SPA (jinja-less) mode.

## Project Setup

This project uses **SPA mode** - a jinja-less configuration where:
- Backend serves API only (no template rendering)
- Frontend is a standalone React SPA
- TypeScript types/SDK auto-generated from OpenAPI schema

## Key Configuration Files

| File | Purpose |
|------|---------|
| `src/py/app/lib/settings.py` | ViteSettings class with ViteConfig |
| `src/py/app/server/plugins.py` | VitePlugin instantiation |
| `src/js/vite.config.ts` | Frontend Vite configuration |
| `src/js/src/lib/generated/` | Auto-generated TypeScript |

## Backend Configuration (Python)

### ViteSettings (`src/py/app/lib/settings.py`)

```python
from litestar_vite import PathConfig, RuntimeConfig, TypeGenConfig, ViteConfig

@dataclass
class ViteSettings:
    DEV_MODE: bool = field(default_factory=get_env("VITE_DEV_MODE", False))
    BUNDLE_DIR: Path = field(default_factory=get_env("VITE_BUNDLE_DIR", STATIC_DIR))
    ASSET_URL: str = field(default_factory=get_env("ASSET_URL", "/"))

    def get_config(self, base_dir: Path = BASE_DIR.parent.parent) -> ViteConfig:
        return ViteConfig(
            mode="spa",  # IMPORTANT: SPA mode, no Jinja templates
            dev_mode=self.DEV_MODE,
            runtime=RuntimeConfig(executor="bun"),  # or "npm", "pnpm"
            paths=PathConfig(
                root=base_dir / "js",
                bundle_dir=self.BUNDLE_DIR,
                asset_url=self.ASSET_URL,
            ),
            types=TypeGenConfig(
                output=base_dir / "js" / "src" / "lib" / "generated",
                openapi_path=base_dir / "js" / "src" / "lib" / "generated" / "openapi.json",
                routes_path=base_dir / "js" / "src" / "lib" / "generated" / "routes.json",
                routes_ts_path=base_dir / "js" / "src" / "lib" / "generated" / "routes.ts",
                generate_zod=True,      # Generate Zod validation schemas
                generate_sdk=True,      # Generate API client SDK
                generate_routes=True,   # Generate route definitions
            ),
        )
```

### Plugin Registration (`src/py/app/server/plugins.py`)

```python
from litestar_vite import VitePlugin
from app import config

vite = VitePlugin(config=config.vite)
```

### Plugin in App Config (`src/py/app/server/core.py`)

```python
app_config.plugins.extend([
    plugins.vite,
    # ... other plugins
])
```

## Frontend Configuration (TypeScript)

### Vite Config (`src/js/vite.config.ts`)

```typescript
import litestar from "litestar-vite-plugin"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [
    // Other plugins first (tanstackRouter, tailwindcss, react)
    litestar({
      input: ["src/main.tsx", "src/styles.css"],
    }),
  ],
})
```

## Generated Files Structure

After running `make types`, the following are generated in `src/js/src/lib/generated/`:

```
generated/
├── api/
│   ├── client/          # HTTP client utilities
│   ├── core/            # Core API utilities
│   ├── client.gen.ts    # Client configuration
│   ├── index.ts         # Main exports
│   ├── schemas.gen.ts   # Serialization schemas
│   ├── sdk.gen.ts       # API SDK functions
│   ├── types.gen.ts     # TypeScript types
│   └── zod.gen.ts       # Zod validation schemas
├── openapi.json         # OpenAPI specification
├── routes.json          # Route definitions (JSON)
└── routes.ts            # Route definitions (TypeScript)
```

## Using Generated API Client

### Import SDK Functions

```typescript
import {
  accountLogin,
  accountRegister,
  listUsers,
  createUser,
  getUser,
  updateUser,
  deleteUser,
} from '@/lib/generated/api'
```

### Import Types

```typescript
import type {
  User,
  UserCreate,
  UserUpdate,
  AccountLogin,
  Message,
} from '@/lib/generated/api'
```

### Import Zod Schemas

```typescript
import {
  UserSchema,
  UserCreateSchema,
  AccountLoginSchema,
} from '@/lib/generated/api/zod.gen'
```

### Example: Login with SDK

```typescript
import { accountLogin } from '@/lib/generated/api'

async function login(email: string, password: string) {
  const response = await accountLogin({
    body: { username: email, password },
  })
  return response.data
}
```

### Example: TanStack Query with SDK

```typescript
import { useQuery, useMutation } from '@tanstack/react-query'
import { listUsers, createUser } from '@/lib/generated/api'
import type { UserCreate } from '@/lib/generated/api'

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await listUsers()
      return response.data
    },
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: UserCreate) => {
      const response = await createUser({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
```

## Type Generation Commands

```bash
# Generate TypeScript types from OpenAPI schema
make types

# This runs:
uv run app assets generate-types
```

**IMPORTANT**: Run `make types` after ANY of these changes:
- Adding/modifying msgspec schemas
- Adding/modifying API endpoints (controllers)
- Changing route paths
- Modifying request/response types

## TypeGenConfig Options

| Option | Default | Description |
|--------|---------|-------------|
| `output` | - | Output directory for generated files |
| `openapi_path` | - | Path for openapi.json |
| `routes_path` | - | Path for routes.json |
| `routes_ts_path` | - | Path for routes.ts |
| `generate_zod` | `False` | Generate Zod validation schemas |
| `generate_sdk` | `False` | Generate API client SDK |
| `generate_routes` | `False` | Generate route definitions |
| `generate_page_props` | `False` | Generate page props (for Inertia) |
| `global_route` | `True` | Export routes globally |

## Development Mode

### Start Development Server

```bash
# Start all services (backend + vite dev server)
uv run app run

# Or separately:
make start-infra  # Start DB/Redis
uv run app run    # Start app with hot reload
```

In dev mode (`VITE_DEV_MODE=true`):
- Vite dev server runs automatically
- Hot module replacement (HMR) enabled
- TypeScript types auto-regenerate on schema changes

### Production Build

```bash
# Build frontend
cd src/js && npm run build

# Or via make
make build
```

## Common Patterns

### Adding New API Endpoint

1. Create controller in `src/py/app/domain/{domain}/controllers/`
2. Create schemas in `src/py/app/domain/{domain}/schemas.py`
3. Register controller in `src/py/app/server/core.py`
4. Add schemas to `signature_namespace`
5. Run `make types`
6. Use generated SDK in frontend

### Using with TanStack Form + Zod

```typescript
import { useForm } from '@tanstack/react-form'
import { zodValidator } from '@tanstack/zod-form-adapter'
import { UserCreateSchema } from '@/lib/generated/api/zod.gen'
import { createUser } from '@/lib/generated/api'

function CreateUserForm() {
  const form = useForm({
    defaultValues: { email: '', name: '' },
    validatorAdapter: zodValidator(),
    validators: { onChange: UserCreateSchema },
    onSubmit: async ({ value }) => {
      await createUser({ body: value })
    },
  })

  // ... form JSX
}
```

## Context7 Lookup

For litestar-vite documentation:

```python
# Use main Litestar docs (includes vite plugin)
mcp__context7__query-docs(
    libraryId="/websites/litestar_dev_2",
    query="VitePlugin ViteConfig SPA mode TypeGenConfig"
)
```

## Troubleshooting

### Types Not Updating

```bash
# Force regenerate
rm -rf src/js/src/lib/generated/*
make types
```

### SDK Functions Missing

Ensure schemas are in `signature_namespace`:

```python
# In server/core.py
app_config.signature_namespace.update({
    **{k: getattr(schemas, k) for k in schemas.__all__},
})
```

### Vite Dev Server Not Starting

Check `VITE_DEV_MODE=true` in `.env` and ensure:
- Node/Bun is installed
- `npm install` has been run in `src/js/`
