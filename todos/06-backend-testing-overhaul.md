# Backend Testing Overhaul

**Priority: HIGH** | **Effort: Large** | **Phase: 3**
**Addresses GitHub Issue #49: Additional Integration Tests**

## Overview
Completely overhaul the backend testing suite to achieve comprehensive coverage of all services, endpoints, and business logic. Update existing tests to current codebase and implement new test patterns using modern testing practices.

## Current State Assessment

### Existing Test Issues
- [ ] **Audit current test suite**
  - Identify outdated tests that don't match current code
  - Find missing test coverage gaps
  - Review test patterns and consistency
  - Check test performance and reliability

## Testing Framework Enhancement

### 1. Test Configuration Updates
- [ ] **Update pytest configuration**
  ```python
  # Update: pyproject.toml [tool.pytest.ini_options]
  testpaths = ["src/py/tests"]
  python_files = ["test_*.py", "*_test.py"]
  python_classes = ["Test*"]
  python_functions = ["test_*"]
  addopts = [
      "--strict-markers",
      "--strict-config",
      "--cov=src/py/app",
      "--cov-report=term-missing",
      "--cov-report=html:htmlcov",
      "--cov-report=xml",
      "--cov-fail-under=90",
      "--asyncio-mode=auto",
      "--tb=short",
      "-v"
  ]
  markers = [
      "unit: marks tests as unit tests (fast, isolated)",
      "integration: marks tests as integration tests (slower, database)",
      "slow: marks tests as slow running tests",
      "auth: marks tests related to authentication",
      "email: marks tests that send emails",
      "external: marks tests that call external services"
  ]
  ```

### 2. Test Fixtures Enhancement
- [ ] **Create comprehensive fixture system**
  ```python
  # File: src/py/tests/conftest.py
  import pytest
  import asyncio
  from typing import AsyncGenerator
  from litestar.testing import AsyncTestClient
  from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
  from advanced_alchemy.extensions.litestar import async_autocommit_before_send
  
  from app.db.models import User, Team, Role, TeamMember
  from app.lib.settings import get_settings
  from app.server.asgi import create_app
  from app.services import UserService, TeamService, RoleService
  
  @pytest.fixture(scope="session")
  def event_loop():
      """Create an instance of the default event loop for the test session."""
      loop = asyncio.get_event_loop_policy().new_event_loop()
      yield loop
      loop.close()
  
  @pytest.fixture(scope="session")
  async def engine():
      """Create test database engine."""
      settings = get_settings()
      engine = create_async_engine(
          settings.db.URL + "_test",  # Use test database
          echo=settings.db.ECHO,
          future=True
      )
      yield engine
      await engine.dispose()
  
  @pytest.fixture
  async def session(engine) -> AsyncGenerator[AsyncSession, None]:
      """Create database session for tests."""
      async with AsyncSession(engine, expire_on_commit=False) as session:
          yield session
  
  @pytest.fixture
  async def client() -> AsyncGenerator[AsyncTestClient, None]:
      """Create test client."""
      app = create_app()
      async with AsyncTestClient(app=app) as client:
          yield client
  
  @pytest.fixture
  async def authenticated_client(client: AsyncTestClient, test_user: User) -> AsyncTestClient:
      """Create authenticated test client."""
      # Login and set auth headers
      login_response = await client.post("/api/access/login", json={
          "username": test_user.email,
          "password": "TestPassword123!"
      })
      token = login_response.json()["access_token"]
      client.headers.update({"Authorization": f"Bearer {token}"})
      return client
  ```

### 3. Test Data Factories
- [ ] **Create test data factories using factory_boy**
  ```python
  # File: src/py/tests/factories.py
  import factory
  from factory.alchemy import SQLAlchemyModelFactory
  from faker import Faker
  
  from app.db.models import User, Team, Role, TeamMember, TeamInvitation
  from app.lib.crypt import get_password_hash
  
  fake = Faker()
  
  class UserFactory(SQLAlchemyModelFactory):
      class Meta:
          model = User
          sqlalchemy_session_persistence = "commit"
      
      id = factory.LazyFunction(lambda: uuid4())
      email = factory.LazyAttribute(lambda obj: fake.email())
      name = factory.LazyAttribute(lambda obj: fake.name())
      hashed_password = factory.LazyFunction(lambda: get_password_hash("TestPassword123!"))
      is_active = True
      is_verified = True
      is_superuser = False
      email_verified_at = factory.LazyFunction(lambda: datetime.utcnow())
  
  class AdminUserFactory(UserFactory):
      is_superuser = True
      email = "admin@test.com"
      name = "Test Admin"
  
  class TeamFactory(SQLAlchemyModelFactory):
      class Meta:
          model = Team
          sqlalchemy_session_persistence = "commit"
      
      id = factory.LazyFunction(lambda: uuid4())
      name = factory.LazyAttribute(lambda obj: fake.company())
      slug = factory.LazyAttribute(lambda obj: fake.slug())
      description = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=200))
      is_active = True
      
      @factory.post_generation
      def owner(self, create, extracted, **kwargs):
          if not create:
              return
          if extracted:
              # Create team membership for owner
              TeamMemberFactory(team=self, user=extracted, role="admin")
  
  class TeamMemberFactory(SQLAlchemyModelFactory):
      class Meta:
          model = TeamMember
          sqlalchemy_session_persistence = "commit"
      
      team = factory.SubFactory(TeamFactory)
      user = factory.SubFactory(UserFactory)
      role = "member"
      is_active = True
  ```

### 4. Fixtures for Common Test Data
- [ ] **Create reusable test data fixtures**
  ```python
  # Add to src/py/tests/conftest.py
  
  @pytest.fixture
  async def test_user(session: AsyncSession) -> User:
      """Create a test user."""
      user = UserFactory.build()
      session.add(user)
      await session.commit()
      await session.refresh(user)
      return user
  
  @pytest.fixture
  async def admin_user(session: AsyncSession) -> User:
      """Create an admin user."""
      user = AdminUserFactory.build()
      session.add(user)
      await session.commit()
      await session.refresh(user)
      return user
  
  @pytest.fixture
  async def test_team(session: AsyncSession, test_user: User) -> Team:
      """Create a test team with owner."""
      team = TeamFactory.build()
      session.add(team)
      await session.commit()
      await session.refresh(team)
      
      # Add owner membership
      membership = TeamMemberFactory.build(team=team, user=test_user, role="admin")
      session.add(membership)
      await session.commit()
      
      return team
  
  @pytest.fixture
  async def test_team_invitation(session: AsyncSession, test_team: Team) -> TeamInvitation:
      """Create a test team invitation."""
      invitation = TeamInvitationFactory.build(team=test_team)
      session.add(invitation)
      await session.commit()
      await session.refresh(invitation)
      return invitation
  ```

## Service Layer Testing

### 1. UserService Tests
- [ ] **Create comprehensive UserService tests**
  ```python
  # File: src/py/tests/unit/services/test_user_service.py
  import pytest
  from uuid import uuid4
  from unittest.mock import AsyncMock, patch
  
  from app.services import UserService
  from app.schemas.accounts import UserCreate, UserUpdate
  from app.db.models import User
  from tests.factories import UserFactory
  
  class TestUserService:
      @pytest.mark.unit
      async def test_create_user_success(self, session, user_service: UserService):
          """Test successful user creation."""
          user_data = UserCreate(
              email="test@example.com",
              password="TestPassword123!",
              name="Test User"
          )
          
          user = await user_service.create(user_data)
          
          assert user.email == "test@example.com"
          assert user.name == "Test User"
          assert user.hashed_password != "TestPassword123!"  # Should be hashed
          assert user.is_active is True
          assert user.is_verified is False  # Should require verification
      
      @pytest.mark.unit
      async def test_create_user_duplicate_email(self, session, user_service: UserService):
          """Test user creation with duplicate email fails."""
          # Create first user
          existing_user = UserFactory.build(email="test@example.com")
          session.add(existing_user)
          await session.commit()
          
          # Try to create second user with same email
          user_data = UserCreate(
              email="test@example.com",
              password="TestPassword123!",
              name="Test User 2"
          )
          
          with pytest.raises(ConflictError):
              await user_service.create(user_data)
      
      @pytest.mark.unit
      async def test_authenticate_success(self, session, user_service: UserService):
          """Test successful user authentication."""
          # Create user with known password
          user = UserFactory.build(
              email="test@example.com",
              hashed_password=get_password_hash("TestPassword123!")
          )
          session.add(user)
          await session.commit()
          
          authenticated_user = await user_service.authenticate(
              "test@example.com",
              "TestPassword123!"
          )
          
          assert authenticated_user is not None
          assert authenticated_user.email == "test@example.com"
      
      @pytest.mark.unit
      async def test_authenticate_wrong_password(self, session, user_service: UserService):
          """Test authentication with wrong password fails."""
          user = UserFactory.build(
              email="test@example.com",
              hashed_password=get_password_hash("TestPassword123!")
          )
          session.add(user)
          await session.commit()
          
          with pytest.raises(PermissionDeniedException):
              await user_service.authenticate("test@example.com", "WrongPassword")
      
      @pytest.mark.unit
      async def test_update_user_success(self, session, user_service: UserService, test_user: User):
          """Test successful user update."""
          update_data = UserUpdate(name="Updated Name")
          
          updated_user = await user_service.update(test_user.id, update_data)
          
          assert updated_user.name == "Updated Name"
          assert updated_user.email == test_user.email  # Should not change
      
      @pytest.mark.unit
      async def test_password_update_success(self, session, user_service: UserService, test_user: User):
          """Test successful password update."""
          new_password = "NewPassword123!"
          
          await user_service.update_password(test_user.id, new_password)
          
          # Verify old password doesn't work
          with pytest.raises(PermissionDeniedException):
              await user_service.authenticate(test_user.email, "TestPassword123!")
          
          # Verify new password works
          authenticated_user = await user_service.authenticate(test_user.email, new_password)
          assert authenticated_user.id == test_user.id
  ```

### 2. TeamService Tests
- [ ] **Create comprehensive TeamService tests**
  ```python
  # File: src/py/tests/unit/services/test_team_service.py
  import pytest
  from app.services import TeamService
  from app.schemas.teams import TeamCreate, TeamUpdate
  from tests.factories import TeamFactory, UserFactory
  
  class TestTeamService:
      @pytest.mark.unit
      async def test_create_team_success(self, session, team_service: TeamService, test_user: User):
          """Test successful team creation."""
          team_data = TeamCreate(
              name="Test Team",
              description="A test team"
          )
          
          team = await team_service.create_team_with_owner(team_data, test_user.id)
          
          assert team.name == "Test Team"
          assert team.description == "A test team"
          assert team.slug is not None
          # Verify owner membership was created
          memberships = await team_service.get_team_members(team.id)
          assert len(memberships) == 1
          assert memberships[0].user_id == test_user.id
          assert memberships[0].role == "admin"
      
      @pytest.mark.unit
      async def test_add_team_member_success(self, session, team_service: TeamService, test_team: Team):
          """Test successfully adding team member."""
          new_user = UserFactory.build()
          session.add(new_user)
          await session.commit()
          
          membership = await team_service.add_team_member(
              test_team.id,
              new_user.id,
              role="member"
          )
          
          assert membership.team_id == test_team.id
          assert membership.user_id == new_user.id
          assert membership.role == "member"
          assert membership.is_active is True
      
      @pytest.mark.unit
      async def test_remove_team_member_success(self, session, team_service: TeamService, test_team: Team):
          """Test successfully removing team member."""
          # Add a member first
          member_user = UserFactory.build()
          session.add(member_user)
          await session.commit()
          
          membership = await team_service.add_team_member(test_team.id, member_user.id)
          
          # Remove the member
          await team_service.remove_team_member(test_team.id, member_user.id)
          
          # Verify member is no longer active
          updated_membership = await team_service.get_team_member(test_team.id, member_user.id)
          assert updated_membership.is_active is False
  ```

### 3. Email Verification Service Tests
- [ ] **Create EmailVerificationService tests**
  ```python
  # File: src/py/tests/unit/services/test_email_verification_service.py
  import pytest
  from datetime import datetime, timedelta
  from unittest.mock import AsyncMock, patch
  
  from app.services import EmailVerificationService
  from app.db.models import EmailVerificationToken
  from tests.factories import UserFactory
  
  class TestEmailVerificationService:
      @pytest.mark.unit
      async def test_create_verification_token(self, session, verification_service: EmailVerificationService, test_user: User):
          """Test verification token creation."""
          token = await verification_service.create_verification_token(test_user.id)
          
          assert token.user_id == test_user.id
          assert token.token is not None
          assert len(token.token) >= 32
          assert token.expires_at > datetime.utcnow()
          assert token.used_at is None
      
      @pytest.mark.unit
      async def test_verify_token_success(self, session, verification_service: EmailVerificationService, test_user: User):
          """Test successful token verification."""
          # Create token
          token = await verification_service.create_verification_token(test_user.id)
          
          # Verify token
          verified_user = await verification_service.verify_token(token.token)
          
          assert verified_user is not None
          assert verified_user.id == test_user.id
          
          # Check token is marked as used
          await session.refresh(token)
          assert token.used_at is not None
      
      @pytest.mark.unit
      async def test_verify_expired_token(self, session, verification_service: EmailVerificationService, test_user: User):
          """Test verification of expired token fails."""
          # Create expired token
          token = EmailVerificationToken(
              user_id=test_user.id,
              token="expired_token",
              expires_at=datetime.utcnow() - timedelta(hours=1)
          )
          session.add(token)
          await session.commit()
          
          # Try to verify expired token
          verified_user = await verification_service.verify_token("expired_token")
          
          assert verified_user is None
      
      @pytest.mark.unit
      async def test_cleanup_expired_tokens(self, session, verification_service: EmailVerificationService):
          """Test cleanup of expired tokens."""
          # Create expired tokens
          expired_token1 = EmailVerificationToken(
              user_id=uuid4(),
              token="expired1",
              expires_at=datetime.utcnow() - timedelta(hours=1)
          )
          expired_token2 = EmailVerificationToken(
              user_id=uuid4(),
              token="expired2",
              expires_at=datetime.utcnow() - timedelta(hours=2)
          )
          # Create valid token
          valid_token = EmailVerificationToken(
              user_id=uuid4(),
              token="valid",
              expires_at=datetime.utcnow() + timedelta(hours=1)
          )
          
          session.add_all([expired_token1, expired_token2, valid_token])
          await session.commit()
          
          # Cleanup expired tokens
          cleaned_count = await verification_service.cleanup_expired_tokens()
          
          assert cleaned_count == 2
          
          # Verify only valid token remains
          remaining_tokens = await session.execute(
              select(EmailVerificationToken).where(EmailVerificationToken.expires_at > datetime.utcnow())
          )
          assert len(remaining_tokens.scalars().all()) == 1
  ```

## Integration Testing

### 1. Authentication Endpoints Integration Tests
- [ ] **Create comprehensive auth endpoint tests**
  ```python
  # File: src/py/tests/integration/test_auth_endpoints.py
  import pytest
  import msgspec
  from litestar.testing import AsyncTestClient
  
  from app.schemas.accounts import UserRead, AccountLogin, AccountRegister
  from tests.factories import UserFactory
  
  class TestAuthEndpoints:
      @pytest.mark.integration
      async def test_signup_success(self, client: AsyncTestClient):
          """Test successful user signup."""
          signup_data = {
              "email": "newuser@example.com",
              "password": "TestPassword123!",
              "name": "New User"
          }
          
          response = await client.post("/api/access/signup", json=signup_data)
          
          assert response.status_code == 201
          user_data = msgspec.json.decode(response.content, type=UserRead)
          assert user_data.email == "newuser@example.com"
          assert user_data.name == "New User"
          assert user_data.is_active is True
          assert user_data.email_verified_at is None  # Should require verification
      
      @pytest.mark.integration
      async def test_signup_duplicate_email(self, client: AsyncTestClient, test_user: User):
          """Test signup with duplicate email fails."""
          signup_data = {
              "email": test_user.email,
              "password": "TestPassword123!",
              "name": "Duplicate User"
          }
          
          response = await client.post("/api/access/signup", json=signup_data)
          
          assert response.status_code == 409  # Conflict
          assert "already exists" in response.json()["detail"].lower()
      
      @pytest.mark.integration
      async def test_login_success(self, client: AsyncTestClient, test_user: User):
          """Test successful login."""
          login_data = {
              "username": test_user.email,
              "password": "TestPassword123!"
          }
          
          response = await client.post("/api/access/login", json=login_data)
          
          assert response.status_code == 200
          token_data = response.json()
          assert "access_token" in token_data
          assert token_data["token_type"] == "Bearer"
      
      @pytest.mark.integration
      async def test_login_wrong_password(self, client: AsyncTestClient, test_user: User):
          """Test login with wrong password fails."""
          login_data = {
              "username": test_user.email,
              "password": "WrongPassword"
          }
          
          response = await client.post("/api/access/login", json=login_data)
          
          assert response.status_code == 401
      
      @pytest.mark.integration
      async def test_get_current_user(self, authenticated_client: AsyncTestClient, test_user: User):
          """Test getting current user profile."""
          response = await authenticated_client.get("/api/me")
          
          assert response.status_code == 200
          user_data = msgspec.json.decode(response.content, type=UserRead)
          assert user_data.id == str(test_user.id)
          assert user_data.email == test_user.email
      
      @pytest.mark.integration
      async def test_update_profile(self, authenticated_client: AsyncTestClient, test_user: User):
          """Test updating user profile."""
          update_data = {
              "name": "Updated Name"
          }
          
          response = await authenticated_client.patch("/api/me", json=update_data)
          
          assert response.status_code == 200
          user_data = msgspec.json.decode(response.content, type=UserRead)
          assert user_data.name == "Updated Name"
          assert user_data.email == test_user.email  # Should not change
  ```

### 2. Team Management Integration Tests
- [ ] **Create team endpoint integration tests**
  ```python
  # File: src/py/tests/integration/test_team_endpoints.py
  import pytest
  import msgspec
  from litestar.testing import AsyncTestClient
  
  from app.schemas.teams import TeamRead, TeamCreate, TeamMemberRead
  from tests.factories import TeamFactory, UserFactory
  
  class TestTeamEndpoints:
      @pytest.mark.integration
      async def test_create_team_success(self, authenticated_client: AsyncTestClient):
          """Test successful team creation."""
          team_data = {
              "name": "Test Team",
              "description": "A test team for integration testing"
          }
          
          response = await authenticated_client.post("/api/teams", json=team_data)
          
          assert response.status_code == 201
          team = msgspec.json.decode(response.content, type=TeamRead)
          assert team.name == "Test Team"
          assert team.description == "A test team for integration testing"
          assert team.slug is not None
      
      @pytest.mark.integration
      async def test_get_user_teams(self, authenticated_client: AsyncTestClient, test_user: User, test_team: Team):
          """Test getting user's teams."""
          response = await authenticated_client.get("/api/teams")
          
          assert response.status_code == 200
          teams = msgspec.json.decode(response.content, type=list[TeamRead])
          assert len(teams) >= 1
          team_ids = [team.id for team in teams]
          assert str(test_team.id) in team_ids
      
      @pytest.mark.integration
      async def test_get_team_details(self, authenticated_client: AsyncTestClient, test_team: Team):
          """Test getting team details."""
          response = await authenticated_client.get(f"/api/teams/{test_team.id}")
          
          assert response.status_code == 200
          team = msgspec.json.decode(response.content, type=TeamRead)
          assert team.id == str(test_team.id)
          assert team.name == test_team.name
      
      @pytest.mark.integration
      async def test_get_team_members(self, authenticated_client: AsyncTestClient, test_team: Team):
          """Test getting team members."""
          response = await authenticated_client.get(f"/api/teams/{test_team.id}/members")
          
          assert response.status_code == 200
          members = msgspec.json.decode(response.content, type=list[TeamMemberRead])
          assert len(members) >= 1  # At least the owner
          
          # Check owner is present
          owner_roles = [member.role for member in members if member.role == "admin"]
          assert len(owner_roles) >= 1
      
      @pytest.mark.integration
      async def test_invite_team_member(self, authenticated_client: AsyncTestClient, test_team: Team):
          """Test inviting a team member."""
          invitation_data = {
              "email": "newmember@example.com",
              "role": "member"
          }
          
          response = await authenticated_client.post(
              f"/api/teams/{test_team.id}/invitations",
              json=invitation_data
          )
          
          assert response.status_code == 201
          invitation = response.json()
          assert invitation["email"] == "newmember@example.com"
          assert invitation["role"] == "member"
          assert invitation["status"] == "pending"
  ```

### 3. API Validation Integration Tests
- [ ] **Create validation integration tests**
  ```python
  # File: src/py/tests/integration/test_validation.py
  import pytest
  from litestar.testing import AsyncTestClient
  
  class TestValidationIntegration:
      @pytest.mark.integration
      async def test_invalid_email_rejected(self, client: AsyncTestClient):
          """Test that invalid emails are rejected."""
          invalid_emails = [
              "notanemail",
              "@example.com",
              "test@",
              "test..test@example.com",
              "test@example",
              "a" * 255 + "@example.com"  # Too long
          ]
          
          for email in invalid_emails:
              signup_data = {
                  "email": email,
                  "password": "TestPassword123!",
                  "name": "Test User"
              }
              
              response = await client.post("/api/access/signup", json=signup_data)
              assert response.status_code == 400, f"Email {email} should be rejected"
      
      @pytest.mark.integration
      async def test_weak_password_rejected(self, client: AsyncTestClient):
          """Test that weak passwords are rejected."""
          weak_passwords = [
              "password",  # Too common
              "12345678",  # No complexity
              "Password",  # Missing number and special char
              "Pass123",   # Too short
              "p" * 129    # Too long
          ]
          
          for password in weak_passwords:
              signup_data = {
                  "email": "test@example.com",
                  "password": password,
                  "name": "Test User"
              }
              
              response = await client.post("/api/access/signup", json=signup_data)
              assert response.status_code == 400, f"Password {password} should be rejected"
      
      @pytest.mark.integration
      async def test_sql_injection_protection(self, client: AsyncTestClient):
          """Test that SQL injection attempts are blocked."""
          sql_injection_attempts = [
              "test'; DROP TABLE users; --@example.com",
              "test@example.com'; INSERT INTO users VALUES ('hacker'); --",
              "test@example.com' OR '1'='1",
          ]
          
          for malicious_email in sql_injection_attempts:
              signup_data = {
                  "email": malicious_email,
                  "password": "TestPassword123!",
                  "name": "Test User"
              }
              
              response = await client.post("/api/access/signup", json=signup_data)
              # Should either be rejected as invalid email or properly sanitized
              assert response.status_code in [400, 409], f"SQL injection attempt should be blocked: {malicious_email}"
  ```

## Mocking and External Service Tests

### 1. Email Service Tests
- [ ] **Create email service tests with mocking**
  ```python
  # File: src/py/tests/unit/test_email_service.py
  import pytest
  from unittest.mock import AsyncMock, patch, MagicMock
  
  from app.services import EmailService
  from app.lib.settings import EmailSettings
  
  class TestEmailService:
      @pytest.fixture
      def email_settings(self):
          return EmailSettings(
              SMTP_HOST="localhost",
              SMTP_PORT=1025,
              EMAIL_DEBUG=True,
              DEFAULT_FROM_EMAIL="test@example.com"
          )
      
      @pytest.fixture
      def email_service(self, email_settings):
          return EmailService(email_settings)
      
      @pytest.mark.unit
      @patch('app.services._email.smtplib.SMTP')
      async def test_send_email_success(self, mock_smtp, email_service):
          """Test successful email sending."""
          mock_server = MagicMock()
          mock_smtp.return_value.__enter__.return_value = mock_server
          
          success = await email_service.send_email(
              to_email="recipient@example.com",
              subject="Test Subject",
              html_content="<h1>Test</h1>",
              text_content="Test"
          )
          
          assert success is True
          mock_server.send_message.assert_called_once()
      
      @pytest.mark.unit
      async def test_send_template_email(self, email_service):
          """Test sending templated email."""
          with patch.object(email_service, 'template_renderer') as mock_renderer:
              mock_renderer.render_template.return_value = ("<h1>Welcome</h1>", "Welcome")
              
              with patch.object(email_service, 'send_email') as mock_send:
                  mock_send.return_value = True
                  
                  success = await email_service.send_template_email(
                      template_name="welcome",
                      to_email="user@example.com",
                      context={"user": {"name": "Test User"}}
                  )
                  
                  assert success is True
                  mock_send.assert_called_once()
                  mock_renderer.render_template.assert_called_once_with("welcome", {"user": {"name": "Test User"}})
  ```

### 2. OAuth Service Tests
- [ ] **Create OAuth service tests**
  ```python
  # File: src/py/tests/unit/test_oauth_service.py
  import pytest
  from unittest.mock import AsyncMock, patch
  
  from app.services import GoogleOAuthService
  from app.lib.settings import OAuthSettings
  
  class TestGoogleOAuthService:
      @pytest.fixture
      def oauth_settings(self):
          return OAuthSettings(
              GOOGLE_CLIENT_ID="test_client_id",
              GOOGLE_CLIENT_SECRET="test_client_secret",
              OAUTH_ENABLED=True
          )
      
      @pytest.fixture
      def oauth_service(self, oauth_settings):
          return GoogleOAuthService(oauth_settings)
      
      @pytest.mark.unit
      async def test_get_authorization_url(self, oauth_service):
          """Test OAuth authorization URL generation."""
          url = await oauth_service.get_authorization_url(
              state="test_state",
              redirect_uri="http://localhost:3000/callback"
          )
          
          assert "accounts.google.com" in url
          assert "test_state" in url
          assert "test_client_id" in url
      
      @pytest.mark.unit
      @patch('httpx.AsyncClient.post')
      async def test_exchange_code_for_token(self, mock_post, oauth_service):
          """Test OAuth code to token exchange."""
          mock_response = AsyncMock()
          mock_response.json.return_value = {
              "access_token": "test_access_token",
              "token_type": "Bearer",
              "expires_in": 3600
          }
          mock_post.return_value = mock_response
          
          token = await oauth_service.exchange_code_for_token(
              code="test_code",
              redirect_uri="http://localhost:3000/callback"
          )
          
          assert token.access_token == "test_access_token"
          mock_post.assert_called_once()
      
      @pytest.mark.unit
      @patch('httpx.AsyncClient.get')
      async def test_get_user_info(self, mock_get, oauth_service):
          """Test getting user info from Google."""
          mock_response = AsyncMock()
          mock_response.json.return_value = {
              "id": "google_user_id",
              "email": "user@gmail.com",
              "name": "Test User",
              "picture": "https://example.com/avatar.jpg"
          }
          mock_get.return_value = mock_response
          
          user_info = await oauth_service.get_user_info("test_access_token")
          
          assert user_info["email"] == "user@gmail.com"
          assert user_info["name"] == "Test User"
          mock_get.assert_called_once()
  ```

## Performance and Load Testing

### 1. Database Performance Tests
- [ ] **Create database performance tests**
  ```python
  # File: src/py/tests/performance/test_database_performance.py
  import pytest
  import time
  from sqlalchemy import text
  
  @pytest.mark.slow
  class TestDatabasePerformance:
      async def test_user_query_performance(self, session):
          """Test user query performance with large dataset."""
          # Create many users
          users = [UserFactory.build() for _ in range(1000)]
          session.add_all(users)
          await session.commit()
          
          # Time the query
          start_time = time.time()
          result = await session.execute(
              text("SELECT * FROM users WHERE email LIKE '%test%' LIMIT 10")
          )
          end_time = time.time()
          
          query_time = end_time - start_time
          assert query_time < 0.1  # Should complete in under 100ms
          assert len(result.fetchall()) <= 10
      
      async def test_team_member_join_performance(self, session):
          """Test team member join query performance."""
          # Create test data
          team = TeamFactory.build()
          users = [UserFactory.build() for _ in range(100)]
          session.add(team)
          session.add_all(users)
          await session.commit()
          
          # Create memberships
          memberships = [
              TeamMemberFactory.build(team=team, user=user) 
              for user in users[:50]
          ]
          session.add_all(memberships)
          await session.commit()
          
          # Time the join query
          start_time = time.time()
          result = await session.execute(
              text("""
                  SELECT u.name, tm.role 
                  FROM users u 
                  JOIN team_members tm ON u.id = tm.user_id 
                  WHERE tm.team_id = :team_id AND tm.is_active = true
              """),
              {"team_id": team.id}
          )
          end_time = time.time()
          
          query_time = end_time - start_time
          assert query_time < 0.05  # Should complete in under 50ms
          assert len(result.fetchall()) == 50
  ```

## Test Utilities and Helpers

### 1. Test Data Builders
- [ ] **Create test data builders for complex scenarios**
  ```python
  # File: src/py/tests/builders.py
  from typing import Optional
  from app.db.models import User, Team, TeamMember
  
  class TeamBuilder:
      """Builder for creating complex team scenarios."""
      
      def __init__(self, session):
          self.session = session
          self.team = None
          self.owner = None
          self.members = []
          self.admins = []
      
      async def with_owner(self, user: Optional[User] = None) -> 'TeamBuilder':
          """Add owner to team."""
          if user is None:
              user = UserFactory.build()
              self.session.add(user)
              await self.session.commit()
          
          if self.team is None:
              self.team = TeamFactory.build()
              self.session.add(self.team)
              await self.session.commit()
          
          membership = TeamMemberFactory.build(
              team=self.team,
              user=user,
              role="admin"
          )
          self.session.add(membership)
          self.owner = user
          return self
      
      async def with_members(self, count: int = 5) -> 'TeamBuilder':
          """Add regular members to team."""
          for _ in range(count):
              user = UserFactory.build()
              self.session.add(user)
              await self.session.commit()
              
              membership = TeamMemberFactory.build(
                  team=self.team,
                  user=user,
                  role="member"
              )
              self.session.add(membership)
              self.members.append(user)
          
          return self
      
      async def build(self) -> Team:
          """Build and return the team."""
          await self.session.commit()
          await self.session.refresh(self.team)
          return self.team
  ```

### 2. Test Assertion Helpers
- [ ] **Create custom assertion helpers**
  ```python
  # File: src/py/tests/assertions.py
  from typing import Any, Dict
  import msgspec
  
  def assert_user_response(response_data: Dict[str, Any], expected_user: User):
      """Assert user response matches expected user."""
      assert response_data["id"] == str(expected_user.id)
      assert response_data["email"] == expected_user.email
      assert response_data["name"] == expected_user.name
      assert response_data["is_active"] == expected_user.is_active
      assert "hashed_password" not in response_data  # Should never be exposed
  
  def assert_team_response(response_data: Dict[str, Any], expected_team: Team):
      """Assert team response matches expected team."""
      assert response_data["id"] == str(expected_team.id)
      assert response_data["name"] == expected_team.name
      assert response_data["slug"] == expected_team.slug
      assert response_data["description"] == expected_team.description
      assert response_data["is_active"] == expected_team.is_active
  
  def assert_validation_error(response, expected_field: str = None):
      """Assert response contains validation error."""
      assert response.status_code == 400
      error_data = response.json()
      assert "detail" in error_data
      if expected_field:
          assert expected_field in str(error_data["detail"]).lower()
  ```

## Test Automation and CI

### 1. Test Commands and Scripts
- [ ] **Create test automation scripts**
  ```bash
  # File: scripts/test.sh
  #!/bin/bash
  set -e
  
  echo "Running backend tests..."
  
  # Setup test database
  export DATABASE_URL="${DATABASE_URL}_test"
  
  # Run database migrations for test DB
  alembic upgrade head
  
  # Run tests with coverage
  pytest src/py/tests/ \
      --cov=src/py/app \
      --cov-report=term-missing \
      --cov-report=html:htmlcov \
      --cov-report=xml \
      --cov-fail-under=90 \
      --tb=short \
      -v
  
  # Cleanup test database
  # (implement database cleanup)
  
  echo "Tests completed successfully!"
  ```

### 2. Continuous Integration Configuration
- [ ] **Update GitHub Actions for testing**
  ```yaml
  # File: .github/workflows/test-backend.yml
  name: Backend Tests
  
  on:
    push:
      branches: [ main, develop ]
      paths: ['src/py/**', 'tests/**', 'pyproject.toml']
    pull_request:
      branches: [ main ]
      paths: ['src/py/**', 'tests/**', 'pyproject.toml']
  
  jobs:
    test:
      runs-on: ubuntu-latest
      
      services:
        postgres:
          image: postgres:15
          env:
            POSTGRES_PASSWORD: postgres
            POSTGRES_DB: litestar_test
          options: >-
            --health-cmd pg_isready
            --health-interval 10s
            --health-timeout 5s
            --health-retries 5
        
        redis:
          image: redis:7
          options: >-
            --health-cmd "redis-cli ping"
            --health-interval 10s
            --health-timeout 5s
            --health-retries 5
      
      steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install UV
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install dependencies
        run: |
          uv sync --dev
          uv pip install pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/litestar_test
          REDIS_URL: redis://localhost:6379
          SECRET_KEY: test_secret_key
        run: |
          uv run pytest src/py/tests/ \
            --cov=src/py/app \
            --cov-report=xml \
            --cov-fail-under=90 \
            -v
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
  ```

## Success Criteria
- [ ] 90%+ test coverage for all service layers
- [ ] 100% coverage for critical authentication/authorization flows
- [ ] All API endpoints have integration tests
- [ ] All database models have unit tests
- [ ] Email and external service mocking works correctly
- [ ] Performance tests validate query efficiency
- [ ] All validation rules have comprehensive tests
- [ ] Test suite runs reliably in CI/CD
- [ ] Clear test documentation and patterns
- [ ] Easy to add new tests following established patterns