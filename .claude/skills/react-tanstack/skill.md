# React + TanStack Skill

Quick reference for React 19 with TanStack Router and Query patterns.

## Context7 Lookup

```python
# TanStack Router
mcp__context7__resolve-library-id(libraryName="tanstack router", query="...")
mcp__context7__query-docs(libraryId="/tanstack/router", query="...")

# TanStack Query
mcp__context7__resolve-library-id(libraryName="tanstack query", query="...")
mcp__context7__query-docs(libraryId="/tanstack/query", query="...")

# React
mcp__context7__resolve-library-id(libraryName="react", query="...")
```

## Project Files

- Routes: `src/js/src/routes/`
- Components: `src/js/src/components/`
- Hooks: `src/js/src/hooks/`
- API: `src/js/src/lib/api/`
- Route tree: `src/js/src/routeTree.gen.ts` (auto-generated)

## TanStack Router Page

```typescript
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/users')({
  component: UsersPage,
})

function UsersPage() {
  return (
    <div>
      <h1>Users</h1>
    </div>
  )
}
```

## Router with Loader

```typescript
import { createFileRoute } from '@tanstack/react-router'
import { queryClient } from '@/lib/query'
import { usersQueryOptions } from '@/hooks/use-users'

export const Route = createFileRoute('/users')({
  loader: () => queryClient.ensureQueryData(usersQueryOptions()),
  component: UsersPage,
})

function UsersPage() {
  const users = Route.useLoaderData()

  return (
    <div>
      {users.map(user => (
        <div key={user.id}>{user.name}</div>
      ))}
    </div>
  )
}
```

## TanStack Query Hook

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

// Query options factory
export const usersQueryOptions = () => ({
  queryKey: ['users'],
  queryFn: () => api.getUsers(),
})

// Use in component
export function useUsers() {
  return useQuery(usersQueryOptions())
}

// Mutation hook
export function useCreateUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UserCreate) => api.createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
```

## Component Pattern

```typescript
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface UserFormProps {
  onSubmit: (data: UserCreate) => void
  isLoading?: boolean
}

export function UserForm({ onSubmit, isLoading }: UserFormProps) {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({ email, name })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <Input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Name"
      />
      <Button type="submit" disabled={isLoading}>
        {isLoading ? 'Creating...' : 'Create User'}
      </Button>
    </form>
  )
}
```

## Form with TanStack Form + Zod

```typescript
import { useForm } from '@tanstack/react-form'
import { zodValidator } from '@tanstack/zod-form-adapter'
import { z } from 'zod'

const userSchema = z.object({
  email: z.string().email('Invalid email'),
  name: z.string().min(1, 'Name required'),
})

export function UserFormValidated() {
  const form = useForm({
    defaultValues: {
      email: '',
      name: '',
    },
    onSubmit: async ({ value }) => {
      console.log(value)
    },
    validatorAdapter: zodValidator(),
    validators: {
      onChange: userSchema,
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        form.handleSubmit()
      }}
    >
      <form.Field
        name="email"
        children={(field) => (
          <div>
            <Input
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(e) => field.handleChange(e.target.value)}
            />
            {field.state.meta.errors.length > 0 && (
              <span className="text-red-500">{field.state.meta.errors.join(', ')}</span>
            )}
          </div>
        )}
      />
      <Button type="submit">Submit</Button>
    </form>
  )
}
```

## Navigation

```typescript
import { Link, useNavigate, useRouter } from '@tanstack/react-router'

// Link component
<Link to="/users/$userId" params={{ userId: user.id }}>
  View User
</Link>

// Programmatic navigation
const navigate = useNavigate()
navigate({ to: '/users/$userId', params: { userId: user.id } })

// Router instance
const router = useRouter()
router.invalidate()  // Refresh current route
```

## Route Parameters

```typescript
// In routes/users/$userId.tsx
export const Route = createFileRoute('/users/$userId')({
  component: UserDetailPage,
})

function UserDetailPage() {
  const { userId } = Route.useParams()
  // userId is typed as string
}
```

## Search Params

```typescript
export const Route = createFileRoute('/users')({
  validateSearch: (search) => ({
    page: Number(search.page) || 1,
    filter: (search.filter as string) || '',
  }),
  component: UsersPage,
})

function UsersPage() {
  const { page, filter } = Route.useSearch()
}
```
