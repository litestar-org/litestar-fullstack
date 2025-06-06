# Best Practices

## Overview

This guide outlines the best practices for developing with the Litestar Fullstack SPA. Following these guidelines ensures code quality, performance, security, and maintainability across the project.

## Code Standards

### Python Code Style

#### Type Annotations

⚠️ **Critical**: Always use type annotations for function signatures and class attributes.

```python
# ✅ Good - Fully typed
async def create_user(
    self,
    email: str,
    password: str,
    name: str | None = None,
) -> User:
    """Create a new user account."""
    ...

# ❌ Bad - Missing types
async def create_user(self, email, password, name=None):
    ...
```

#### Async/Await Patterns

All I/O operations must be async:

```python
# ✅ Good - Async all the way
async def get_user_with_teams(self, user_id: UUID) -> UserWithTeams:
    """Get user with their teams."""
    user = await self.users_service.get(user_id)
    teams = await self.teams_service.list(user_id=user_id)
    return UserWithTeams(user=user, teams=teams)

# ❌ Bad - Blocking call in async function
async def get_user_data(self, user_id: UUID) -> dict:
    user = await self.users_service.get(user_id)
    # This blocks the event loop!
    teams = requests.get(f"/api/teams?user_id={user_id}").json()
    return {"user": user, "teams": teams}
```

#### Service Layer Patterns

⚠️ **Critical**: Always use the inner `Repo` pattern for services.

```python
# ✅ Good - Proper service structure
class ProductService(service.SQLAlchemyAsyncRepositoryService[m.Product]):
    """Service for product operations."""
    
    class Repo(repository.SQLAlchemyAsyncRepository[m.Product]):
        """Product repository."""
        model_type = m.Product
    
    repository_type = Repo
    
    async def get_by_category(self, category_id: UUID) -> list[m.Product]:
        """Get products by category."""
        return await self.repository.list(
            m.Product.category_id == category_id,
            m.Product.is_active == True,
        )

# ❌ Bad - Direct database access
class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_products(self):
        result = await self.session.execute(select(Product))
        return result.scalars().all()
```

### TypeScript Code Style

#### Type Safety

Never use `any` type:

```typescript
// ✅ Good - Properly typed
interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

async function fetchUser(id: string): Promise<UserRead> {
  const response = await api.users.getUser({ userId: id });
  return response;
}

// ❌ Bad - Using any
async function fetchData(endpoint: any): Promise<any> {
  const response = await fetch(endpoint);
  return response.json();
}
```

#### Component Patterns

Use functional components with proper typing:

```typescript
// ✅ Good - Typed functional component
interface UserCardProps {
  user: UserRead;
  onEdit?: (user: UserRead) => void;
  className?: string;
}

export function UserCard({ user, onEdit, className }: UserCardProps) {
  return (
    <Card className={cn("hover:shadow-lg", className)}>
      <CardHeader>
        <CardTitle>{user.name || user.email}</CardTitle>
      </CardHeader>
      {onEdit && (
        <CardFooter>
          <Button onClick={() => onEdit(user)} size="sm">
            Edit
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}

// ❌ Bad - Untyped props
export function UserCard(props) {
  return <div>{props.user.name}</div>;
}
```

## Performance Optimization

### Database Performance

#### Query Optimization

Prevent N+1 queries with proper loading strategies:

```python
# ✅ Good - Eager loading relationships
users = await self.repository.list(
    User.is_active == True,
    load=[
        selectinload(User.teams).options(
            joinedload(TeamMember.team, innerjoin=True)
        ),
        selectinload(User.roles),
    ],
)

# ❌ Bad - N+1 query problem
users = await self.repository.list()
for user in users:
    # This executes a query for each user!
    teams = await self.teams_service.list(user_id=user.id)
```

#### Indexing Strategy

Add indexes for frequently queried columns:

```python
class User(UUIDAuditBase):
    """User model with proper indexing."""
    
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True  # Single column index
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_user_active_created", "is_active", "created_at"),
        Index("ix_user_email_active", "email", "is_active"),
    )
```

#### Pagination

Always paginate large datasets:

```python
# ✅ Good - Paginated response
async def list_products(
    self,
    page: int = 1,
    page_size: int = 20,
    filters: dict | None = None,
) -> PaginatedResponse[Product]:
    """List products with pagination."""
    # Count total
    total = await self.repository.count(**filters)
    
    # Get page
    items = await self.repository.list(
        **filters,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )
```

### Frontend Performance

#### Code Splitting

Lazy load large components:

```typescript
// ✅ Good - Lazy loaded route
const AdminDashboard = lazy(() => import("@/components/admin/dashboard"));

export const Route = createFileRoute("/_app/admin")({
  component: () => (
    <Suspense fallback={<LoadingSpinner />}>
      <AdminDashboard />
    </Suspense>
  ),
});
```

#### Memoization

Optimize expensive computations:

```typescript
// ✅ Good - Memoized calculations
export function TeamMembersList({ members }: { members: TeamMember[] }) {
  const sortedMembers = useMemo(
    () => members.sort((a, b) => a.joinedAt.localeCompare(b.joinedAt)),
    [members]
  );
  
  const membersByRole = useMemo(
    () => groupBy(sortedMembers, "role"),
    [sortedMembers]
  );
  
  return (
    <div>
      {Object.entries(membersByRole).map(([role, roleMembers]) => (
        <RoleSection key={role} role={role} members={roleMembers} />
      ))}
    </div>
  );
}

// Component memoization
const RoleSection = memo(({ role, members }) => {
  return (
    <div>
      <h3>{role}</h3>
      {members.map(member => (
        <MemberCard key={member.id} member={member} />
      ))}
    </div>
  );
});
```

#### React Query Optimization

Configure stale times and caching:

```typescript
// ✅ Good - Optimized query configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: (failureCount, error) => {
        if (error.status === 404) return false;
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
    },
  },
});

// Prefetch critical data
export function usePrefetchUserData(userId: string) {
  const queryClient = useQueryClient();
  
  useEffect(() => {
    // Prefetch user data
    queryClient.prefetchQuery({
      queryKey: ["user", userId],
      queryFn: () => api.users.getUser({ userId }),
    });
    
    // Prefetch user's teams
    queryClient.prefetchQuery({
      queryKey: ["user", userId, "teams"],
      queryFn: () => api.users.getUserTeams({ userId }),
    });
  }, [userId, queryClient]);
}
```

## Security Best Practices

### Input Validation

⚠️ **Critical**: Always validate inputs at every layer.

#### Backend Validation

```python
# ✅ Good - Comprehensive validation
class UserCreate(msgspec.Struct):
    """User creation with validation."""
    email: str = msgspec.field(validator=validate_email)
    password: str = msgspec.field(validator=validate_password_strength)
    name: str | None = msgspec.field(
        default=None,
        validator=lambda x: x is None or (len(x) >= 2 and len(x) <= 100)
    )

def validate_email(email: str) -> str:
    """Validate email format."""
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise ValueError("Invalid email format")
    if len(email) > 255:
        raise ValueError("Email too long")
    return email.lower()

def validate_password_strength(password: str) -> str:
    """Validate password meets requirements."""
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain uppercase letter")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain digit")
    return password
```

#### Frontend Validation

```typescript
// ✅ Good - Zod schema validation
const createUserSchema = z.object({
  email: z.string()
    .email("Invalid email address")
    .max(255, "Email too long"),
  password: z.string()
    .min(12, "Password must be at least 12 characters")
    .regex(/[A-Z]/, "Password must contain uppercase letter")
    .regex(/[0-9]/, "Password must contain digit"),
  name: z.string()
    .min(2, "Name too short")
    .max(100, "Name too long")
    .optional(),
});

// Use in forms
const form = useForm<CreateUserData>({
  resolver: zodResolver(createUserSchema),
});
```

### Authentication Security

#### Token Handling

```typescript
// ✅ Good - Secure token storage
class AuthStore {
  private token: string | null = null;
  
  setToken(token: string) {
    this.token = token;
    // Store in memory only, not localStorage
    // Or use httpOnly cookies
  }
  
  getToken(): string | null {
    return this.token;
  }
  
  clearToken() {
    this.token = null;
  }
}

// ❌ Bad - Insecure storage
localStorage.setItem("token", token); // Vulnerable to XSS
```

#### CORS Configuration

```python
# ✅ Good - Restrictive CORS
from litestar.middleware.cors import CORSConfig

cors_config = CORSConfig(
    allow_origins=["https://yourdomain.com"],  # Specific origins
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
    max_age=3600,
)

# ❌ Bad - Too permissive
cors_config = CORSConfig(
    allow_origins=["*"],  # Allows any origin!
    allow_headers=["*"],
    allow_methods=["*"],
)
```

### SQL Injection Prevention

Always use parameterized queries:

```python
# ✅ Good - Parameterized query
async def search_users(self, search_term: str) -> list[User]:
    """Search users safely."""
    return await self.repository.list(
        User.name.ilike(f"%{search_term}%")  # SQLAlchemy escapes this
    )

# ❌ Bad - SQL injection vulnerability
async def search_users(self, search_term: str) -> list[User]:
    # NEVER DO THIS!
    query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"
    return await self.session.execute(text(query))
```

## Testing Best Practices

### Test Structure

Organize tests to mirror source code:

```
tests/
├── unit/
│   ├── test_services/
│   │   ├── test_users.py
│   │   └── test_teams.py
│   ├── test_models/
│   └── test_utils/
├── integration/
│   ├── test_auth_flow.py
│   └── test_api_endpoints.py
└── conftest.py  # Shared fixtures
```

### Writing Good Tests

#### Descriptive Test Names

```python
# ✅ Good - Clear test names
async def test_create_user_with_valid_data_succeeds():
    """Test that creating a user with valid data succeeds."""

async def test_create_user_with_duplicate_email_raises_error():
    """Test that creating a user with duplicate email raises error."""

async def test_authenticate_with_invalid_password_fails():
    """Test that authentication with wrong password fails."""

# ❌ Bad - Vague test names
async def test_user():
    """Test user."""

async def test_auth():
    """Test auth."""
```

#### Test Isolation

```python
# ✅ Good - Isolated test with fixtures
@pytest.fixture
async def test_user(users_service: UserService) -> User:
    """Create a test user."""
    user = await users_service.create({
        "email": f"test-{uuid4()}@example.com",
        "password": "TestPassword123!",
        "name": "Test User",
    })
    yield user
    # Cleanup
    await users_service.delete(user.id)

async def test_user_can_join_team(
    test_user: User,
    test_team: Team,
    teams_service: TeamService,
):
    """Test that a user can join a team."""
    member = await teams_service.add_member(
        team_id=test_team.id,
        user_id=test_user.id,
        role="MEMBER",
    )
    
    assert member.user_id == test_user.id
    assert member.team_id == test_team.id
    assert member.role == "MEMBER"
```

### Frontend Testing

#### Component Testing

```typescript
// ✅ Good - Comprehensive component test
describe("TeamCard", () => {
  const mockTeam: TeamRead = {
    id: "123",
    name: "Engineering",
    description: "Engineering team",
    ownerId: "456",
    createdAt: "2024-01-01",
    updatedAt: "2024-01-01",
  };
  
  it("renders team information correctly", () => {
    render(<TeamCard team={mockTeam} />);
    
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Engineering team")).toBeInTheDocument();
  });
  
  it("shows owner badge when user is owner", () => {
    render(<TeamCard team={mockTeam} isOwner />);
    
    expect(screen.getByText("Owner")).toBeInTheDocument();
  });
  
  it("calls onEdit when edit button clicked", async () => {
    const onEdit = vi.fn();
    const user = userEvent.setup();
    
    render(<TeamCard team={mockTeam} onEdit={onEdit} />);
    
    await user.click(screen.getByRole("button", { name: /edit/i }));
    
    expect(onEdit).toHaveBeenCalledWith(mockTeam);
  });
  
  it("is accessible", async () => {
    const { container } = render(<TeamCard team={mockTeam} />);
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

## Error Handling

### Backend Error Handling

Use custom exceptions with meaningful messages:

```python
# ✅ Good - Structured error handling
class TeamService(service.SQLAlchemyAsyncRepositoryService[m.Team]):
    async def add_member(
        self,
        team_id: UUID,
        user_id: UUID,
        role: str = "MEMBER",
    ) -> TeamMember:
        """Add user to team with proper error handling."""
        # Check team exists
        team = await self.get_one_or_none(id=team_id)
        if not team:
            raise ResourceNotFoundException(
                detail=f"Team {team_id} not found"
            )
        
        # Check user not already member
        existing = await self.members_repo.get_one_or_none(
            team_id=team_id,
            user_id=user_id,
        )
        if existing:
            raise ClientException(
                detail="User is already a team member",
                status_code=409,  # Conflict
            )
        
        # Check team not full
        member_count = await self.members_repo.count(team_id=team_id)
        if member_count >= team.max_members:
            raise ClientException(
                detail=f"Team has reached maximum of {team.max_members} members",
                status_code=400,
            )
        
        # Add member
        try:
            return await self.members_repo.add(
                TeamMember(
                    team_id=team_id,
                    user_id=user_id,
                    role=role,
                )
            )
        except IntegrityError as e:
            logger.error("Failed to add team member", error=str(e))
            raise ApplicationException(
                detail="Failed to add team member",
                status_code=500,
            )
```

### Frontend Error Handling

Provide meaningful error messages to users:

```typescript
// ✅ Good - User-friendly error handling
export function CreateTeamForm() {
  const createTeam = useCreateTeam();
  const { toast } = useToast();
  
  const handleSubmit = async (data: CreateTeamData) => {
    try {
      const team = await createTeam.mutateAsync(data);
      toast({
        title: "Team created",
        description: `${team.name} has been created successfully.`,
      });
      navigate({ to: "/teams/$teamId", params: { teamId: team.id } });
    } catch (error) {
      // Handle specific errors
      if (error.status === 409) {
        toast({
          title: "Team name taken",
          description: "A team with this name already exists.",
          variant: "destructive",
        });
      } else if (error.status === 402) {
        toast({
          title: "Team limit reached",
          description: "Upgrade your plan to create more teams.",
          variant: "destructive",
          action: <Button size="sm">Upgrade</Button>,
        });
      } else {
        // Generic error
        toast({
          title: "Error creating team",
          description: error.message || "Please try again later.",
          variant: "destructive",
        });
      }
    }
  };
  
  return (
    <Form onSubmit={handleSubmit}>
      {/* Form fields */}
    </Form>
  );
}
```

## Documentation

### Code Documentation

Document complex logic and public APIs:

```python
# ✅ Good - Well documented
class EmailService:
    """Service for sending transactional emails.
    
    This service handles all email operations including:
    - User verification emails
    - Password reset emails
    - Team invitations
    - Activity notifications
    
    Configuration is handled via environment variables.
    See `EmailSettings` for available options.
    
    Example:
        email_service = EmailService(
            base_url="https://app.example.com",
            app_name="My App"
        )
        await email_service.send_verification_email(user, token)
    """
    
    async def send_verification_email(
        self,
        user: User,
        token: EmailVerificationToken,
    ) -> None:
        """Send email verification link to user.
        
        Args:
            user: User to send email to
            token: Verification token object
            
        Raises:
            EmailDeliveryError: If email fails to send
            
        Note:
            The token expires after 24 hours.
            Users can request a new token if needed.
        """
```

### API Documentation

Use OpenAPI annotations:

```python
# ✅ Good - Comprehensive API docs
@post(
    path="/api/teams/{team_id:uuid}/members",
    operation_id="AddTeamMember",
    summary="Add member to team",
    description="""
    Add a user to a team with a specific role.
    
    Requires team owner or admin role.
    The user will receive an email notification.
    """,
    responses={
        201: Response(description="Member added successfully"),
        400: Response(description="Invalid request data"),
        403: Response(description="Insufficient permissions"),
        404: Response(description="Team or user not found"),
        409: Response(description="User already a member"),
    },
    tags=["teams"],
)
async def add_team_member(
    self,
    team_id: Annotated[UUID, Parameter(description="Team ID")],
    data: Annotated[AddMemberRequest, Body(description="Member details")],
    teams_service: TeamService,
    current_user: User,
) -> TeamMemberRead:
    """Add member to team."""
```

## Monitoring and Logging

### Structured Logging

Use structured logging for better observability:

```python
# ✅ Good - Structured logging
import structlog

logger = structlog.get_logger()

async def process_payment(
    self,
    user_id: UUID,
    amount: Decimal,
    currency: str = "USD",
) -> Payment:
    """Process payment with detailed logging."""
    logger.info(
        "Processing payment",
        user_id=str(user_id),
        amount=float(amount),
        currency=currency,
    )
    
    try:
        payment = await self.payment_provider.charge(
            user_id=user_id,
            amount=amount,
            currency=currency,
        )
        
        logger.info(
            "Payment successful",
            user_id=str(user_id),
            payment_id=payment.id,
            amount=float(amount),
        )
        
        return payment
        
    except PaymentError as e:
        logger.error(
            "Payment failed",
            user_id=str(user_id),
            amount=float(amount),
            error=str(e),
            error_code=e.code,
        )
        raise
```

### Performance Monitoring

Add timing to critical operations:

```python
# ✅ Good - Performance tracking
from contextlib import asynccontextmanager
import time

@asynccontextmanager
async def track_performance(operation: str):
    """Track operation performance."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        logger.info(
            "Operation completed",
            operation=operation,
            duration_ms=round(duration * 1000, 2),
        )

async def generate_report(self, team_id: UUID) -> Report:
    """Generate team report with performance tracking."""
    async with track_performance("generate_team_report"):
        # Expensive operation
        data = await self._gather_report_data(team_id)
        report = await self._process_report_data(data)
        return report
```

## Deployment Checklist

Before deploying to production:

### Code Quality
- [ ] All tests pass (`make test-all`)
- [ ] No linting errors (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Documentation is updated
- [ ] OpenAPI schema is current

### Security
- [ ] Environment variables are set correctly
- [ ] Secrets are not committed
- [ ] CORS is properly configured
- [ ] Rate limiting is enabled
- [ ] SSL/TLS is configured

### Performance
- [ ] Database queries are optimized
- [ ] Caching is configured
- [ ] Static assets are minified
- [ ] Code splitting is implemented
- [ ] Monitoring is set up

### Infrastructure
- [ ] Database backups are configured
- [ ] Log aggregation is set up
- [ ] Error tracking is enabled
- [ ] Health checks are working
- [ ] Scaling policies are defined

## Summary

Following these best practices ensures:

1. **Code Quality** - Maintainable, readable code
2. **Performance** - Fast, responsive application
3. **Security** - Protected against common vulnerabilities
4. **Reliability** - Robust error handling and testing
5. **Scalability** - Patterns that grow with your needs

Remember: These are guidelines, not rigid rules. Use your judgment and adapt them to your specific needs while maintaining the core principles of quality, security, and performance.

---

*Great code is not just about making it work—it's about making it work well, securely, and maintainably for the long term.*