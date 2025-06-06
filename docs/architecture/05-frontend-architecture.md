# Frontend Architecture

## Overview

The frontend is built with React 19, TypeScript, and modern tooling to provide a fast, type-safe, and maintainable single-page application. It leverages auto-generated API clients, file-based routing, and a component library for rapid development.

## Technology Stack

### Core Technologies

- **React 19** - Latest React with improved performance and DX
- **TypeScript** - Full type safety across the application
- **Vite** - Lightning-fast build tool with HMR
- **TanStack Router** - Type-safe, file-based routing
- **TanStack Query** - Powerful data synchronization
- **shadcn/ui** - High-quality, customizable components
- **Tailwind CSS v4** - Utility-first styling

### Development Tools

- **Biome** - Fast linting and formatting
- **OpenAPI TypeScript** - Auto-generated API types
- **React Hook Form** - Performant form handling
- **Zod** - Runtime type validation

## Project Structure

```
src/
├── components/              # Reusable components
│   ├── ui/                  # shadcn/ui base components
│   ├── auth/                # Authentication components
│   ├── teams/               # Team-related components
│   └── admin/               # Admin interfaces
├── routes/                  # File-based routing
│   ├── __root.tsx           # Root layout
│   ├── _app.tsx             # Authenticated layout
│   ├── _public.tsx          # Public layout
│   └── _app/                # Protected routes
├── lib/                     # Utilities and clients
│   ├── api/                 # Generated API client
│   ├── auth.ts              # Auth utilities
│   └── utils.ts             # Helper functions
├── hooks/                   # Custom React hooks
└── styles.css               # Global styles
```

## Component Architecture

### Component Patterns

Components follow a consistent structure with TypeScript interfaces:

```typescript
// components/teams/team-card.tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TeamRead } from "@/lib/api/types.gen";

interface TeamCardProps {
  team: TeamRead;
  onEdit?: (team: TeamRead) => void;
  isOwner?: boolean;
}

export function TeamCard({ team, onEdit, isOwner = false }: TeamCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{team.name}</CardTitle>
          {isOwner && <Badge>Owner</Badge>}
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">{team.description}</p>
        {onEdit && (
          <Button 
            onClick={() => onEdit(team)} 
            variant="outline" 
            size="sm"
            className="mt-4"
          >
            Edit Team
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
```

### shadcn/ui Components

Base UI components are from shadcn/ui, customized for the project:

```typescript
// components/ui/button.tsx
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };
```

## Routing System

### File-Based Routes

TanStack Router uses file-based routing with layouts:

```typescript
// routes/__root.tsx - Root layout
import { Outlet, createRootRoute } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";

export const Route = createRootRoute({
  component: () => (
    <>
      <Outlet />
      <TanStackRouterDevtools />
    </>
  ),
});
```

```typescript
// routes/_app.tsx - Authenticated layout
import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { AppLayout } from "@/layouts/app-layout";

export const Route = createFileRoute("/_app")({
  beforeLoad: async ({ context }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/login",
        search: {
          redirect: location.href,
        },
      });
    }
  },
  component: () => (
    <AppLayout>
      <Outlet />
    </AppLayout>
  ),
});
```

### Route Parameters

Dynamic routes with type-safe parameters:

```typescript
// routes/_app/teams/$teamId.tsx
import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

const teamParamsSchema = z.object({
  teamId: z.string().uuid(),
});

export const Route = createFileRoute("/_app/teams/$teamId")({
  params: {
    parse: (params) => teamParamsSchema.parse(params),
    stringify: (params) => params,
  },
  loader: async ({ params, context }) => {
    const team = await context.api.teams.getTeam({ 
      teamId: params.teamId 
    });
    return { team };
  },
  component: TeamDetailPage,
});

function TeamDetailPage() {
  const { team } = Route.useLoaderData();
  const { teamId } = Route.useParams();
  
  return <TeamDetail team={team} />;
}
```

## Data Management

### TanStack Query Integration

Data fetching with caching and synchronization:

```typescript
// hooks/use-teams.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useTeams() {
  return useQuery({
    queryKey: ["teams"],
    queryFn: () => api.teams.listTeams(),
  });
}

export function useCreateTeam() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: TeamCreate) => api.teams.createTeam({ 
      requestBody: data 
    }),
    onSuccess: () => {
      // Invalidate and refetch teams
      queryClient.invalidateQueries({ queryKey: ["teams"] });
    },
  });
}

export function useTeam(teamId: string) {
  return useQuery({
    queryKey: ["teams", teamId],
    queryFn: () => api.teams.getTeam({ teamId }),
    enabled: !!teamId,
  });
}
```

### Optimistic Updates

Immediate UI updates with rollback on error:

```typescript
export function useUpdateTeam(teamId: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: TeamUpdate) => 
      api.teams.updateTeam({ teamId, requestBody: data }),
    
    onMutate: async (newData) => {
      // Cancel in-flight queries
      await queryClient.cancelQueries({ 
        queryKey: ["teams", teamId] 
      });
      
      // Snapshot previous value
      const previousTeam = queryClient.getQueryData(["teams", teamId]);
      
      // Optimistically update
      queryClient.setQueryData(["teams", teamId], (old) => ({
        ...old,
        ...newData,
      }));
      
      return { previousTeam };
    },
    
    onError: (err, newData, context) => {
      // Rollback on error
      if (context?.previousTeam) {
        queryClient.setQueryData(
          ["teams", teamId], 
          context.previousTeam
        );
      }
    },
    
    onSettled: () => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ 
        queryKey: ["teams", teamId] 
      });
    },
  });
}
```

## API Client

### Auto-Generated Types

Types are generated from the OpenAPI schema:

```typescript
// lib/api/types.gen.ts (auto-generated)
export interface UserRead {
  id: string;
  email: string;
  name?: string | null;
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface TeamRead {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  ownerId: string;
  createdAt: string;
  updatedAt: string;
}
```

### API Client Configuration

```typescript
// lib/api/client.gen.ts
import { createClient } from "@hey-api/client-fetch";

export const client = createClient({
  baseUrl: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth interceptor
client.interceptors.request.use((request, options) => {
  const token = getAuthToken();
  if (token) {
    request.headers.set("Authorization", `Bearer ${token}`);
  }
  return request;
});

// Add error interceptor
client.interceptors.response.use(undefined, (error) => {
  if (error.response?.status === 401) {
    // Handle unauthorized
    window.location.href = "/login";
  }
  return Promise.reject(error);
});
```

## Authentication Flow

### Authentication Hook

```typescript
// hooks/use-auth.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  token: string | null;
  user: UserRead | null;
  isAuthenticated: boolean;
  login: (token: string, user: UserRead) => void;
  logout: () => void;
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      
      login: (token, user) => set({
        token,
        user,
        isAuthenticated: true,
      }),
      
      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        });
        window.location.href = "/login";
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ 
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
```

### Login Component with 2FA

```typescript
// components/auth/login.tsx
export function LoginForm() {
  const [requires2FA, setRequires2FA] = useState(false);
  const [tempToken, setTempToken] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const loginMutation = useMutation({
    mutationFn: (data: LoginCredentials) => 
      api.auth.login({ requestBody: data }),
    onSuccess: (response) => {
      if (response.requires2fa) {
        setRequires2FA(true);
        setTempToken(response.tempToken!);
      } else {
        login(response.accessToken!, response.user!);
        navigate({ to: "/home" });
      }
    },
  });
  
  const verify2FAMutation = useMutation({
    mutationFn: (code: string) => 
      api.twoFactor.verify({ 
        requestBody: { tempToken: tempToken!, code } 
      }),
    onSuccess: (response) => {
      login(response.accessToken!, response.user!);
      navigate({ to: "/home" });
    },
  });
  
  if (requires2FA) {
    return (
      <TwoFactorVerification
        onVerify={(code) => verify2FAMutation.mutate(code)}
        isLoading={verify2FAMutation.isPending}
        error={verify2FAMutation.error?.message}
      />
    );
  }
  
  return (
    <Form onSubmit={loginMutation.mutate}>
      {/* Login form fields */}
    </Form>
  );
}
```

## Forms and Validation

### React Hook Form with Zod

Type-safe forms with validation:

```typescript
// components/teams/create-team-form.tsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const createTeamSchema = z.object({
  name: z.string()
    .min(3, "Name must be at least 3 characters")
    .max(50, "Name must be less than 50 characters"),
  description: z.string()
    .max(200, "Description must be less than 200 characters")
    .optional(),
});

type CreateTeamData = z.infer<typeof createTeamSchema>;

export function CreateTeamForm() {
  const createTeam = useCreateTeam();
  
  const form = useForm<CreateTeamData>({
    resolver: zodResolver(createTeamSchema),
    defaultValues: {
      name: "",
      description: "",
    },
  });
  
  const onSubmit = async (data: CreateTeamData) => {
    try {
      await createTeam.mutateAsync(data);
      toast({
        title: "Team created",
        description: "Your team has been created successfully.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create team. Please try again.",
        variant: "destructive",
      });
    }
  };
  
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Team Name</FormLabel>
              <FormControl>
                <Input placeholder="My Awesome Team" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea 
                  placeholder="What's this team about?"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <Button 
          type="submit" 
          disabled={createTeam.isPending}
          className="w-full"
        >
          {createTeam.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating...
            </>
          ) : (
            "Create Team"
          )}
        </Button>
      </form>
    </Form>
  );
}
```

## State Management

### Context for Global State

```typescript
// lib/team-context.tsx
interface TeamContextValue {
  currentTeam: TeamRead | null;
  setCurrentTeam: (team: TeamRead | null) => void;
  isLoading: boolean;
}

const TeamContext = createContext<TeamContextValue | undefined>(undefined);

export function TeamProvider({ children }: { children: ReactNode }) {
  const [currentTeam, setCurrentTeam] = useState<TeamRead | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Load initial team
  useEffect(() => {
    const loadTeam = async () => {
      const savedTeamId = localStorage.getItem("currentTeamId");
      if (savedTeamId) {
        try {
          const team = await api.teams.getTeam({ teamId: savedTeamId });
          setCurrentTeam(team);
        } catch (error) {
          console.error("Failed to load team:", error);
        }
      }
      setIsLoading(false);
    };
    
    loadTeam();
  }, []);
  
  const handleSetCurrentTeam = (team: TeamRead | null) => {
    setCurrentTeam(team);
    if (team) {
      localStorage.setItem("currentTeamId", team.id);
    } else {
      localStorage.removeItem("currentTeamId");
    }
  };
  
  return (
    <TeamContext.Provider 
      value={{
        currentTeam,
        setCurrentTeam: handleSetCurrentTeam,
        isLoading,
      }}
    >
      {children}
    </TeamContext.Provider>
  );
}

export function useTeamContext() {
  const context = useContext(TeamContext);
  if (!context) {
    throw new Error("useTeamContext must be used within TeamProvider");
  }
  return context;
}
```

## Performance Optimization

### Code Splitting

Lazy load routes for better performance:

```typescript
// routes/_app/admin.tsx
import { lazy } from "react";

const AdminDashboard = lazy(() => 
  import("@/components/admin/admin-dashboard")
    .then(m => ({ default: m.AdminDashboard }))
);

export const Route = createFileRoute("/_app/admin")({
  component: () => (
    <Suspense fallback={<LoadingSpinner />}>
      <AdminDashboard />
    </Suspense>
  ),
});
```

### React Query Optimization

```typescript
// Prefetch data
const prefetchTeams = async () => {
  await queryClient.prefetchQuery({
    queryKey: ["teams"],
    queryFn: () => api.teams.listTeams(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Infinite queries for pagination
const useInfiniteTeams = () => {
  return useInfiniteQuery({
    queryKey: ["teams", "infinite"],
    queryFn: ({ pageParam = 1 }) => 
      api.teams.listTeams({ page: pageParam, pageSize: 20 }),
    getNextPageParam: (lastPage, pages) => 
      lastPage.hasMore ? pages.length + 1 : undefined,
  });
};
```

## Testing

### Component Testing

```typescript
// __tests__/components/team-card.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TeamCard } from "@/components/teams/team-card";

describe("TeamCard", () => {
  const mockTeam: TeamRead = {
    id: "123",
    name: "Test Team",
    slug: "test-team",
    description: "A test team",
    ownerId: "456",
    createdAt: "2024-01-01",
    updatedAt: "2024-01-01",
  };
  
  it("renders team information", () => {
    render(<TeamCard team={mockTeam} />);
    
    expect(screen.getByText("Test Team")).toBeInTheDocument();
    expect(screen.getByText("A test team")).toBeInTheDocument();
  });
  
  it("shows owner badge when isOwner is true", () => {
    render(<TeamCard team={mockTeam} isOwner />);
    
    expect(screen.getByText("Owner")).toBeInTheDocument();
  });
  
  it("calls onEdit when edit button is clicked", async () => {
    const onEdit = vi.fn();
    const user = userEvent.setup();
    
    render(<TeamCard team={mockTeam} onEdit={onEdit} />);
    
    await user.click(screen.getByText("Edit Team"));
    
    expect(onEdit).toHaveBeenCalledWith(mockTeam);
  });
});
```

## Best Practices

### 1. Component Organization

- Keep components small and focused
- Extract reusable logic into hooks
- Use composition over inheritance
- Implement proper error boundaries

### 2. Type Safety

- Use generated types from API
- Avoid `any` types
- Validate runtime data with Zod
- Use strict TypeScript config

### 3. Performance

- Memoize expensive computations
- Use React.memo for pure components
- Implement virtualization for long lists
- Optimize bundle size with code splitting

### 4. Accessibility

- Use semantic HTML
- Add proper ARIA labels
- Ensure keyboard navigation
- Test with screen readers

## Next Steps

Now that you understand the frontend architecture:

1. Review [Development Workflow](06-development-workflow.md) for commands
2. Check [Best Practices](07-best-practices.md) for guidelines
3. Start building features!

---

*The frontend architecture prioritizes developer experience, type safety, and performance. Following these patterns ensures a maintainable and scalable application.*