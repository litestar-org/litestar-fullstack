"""Integration tests for validation and security features."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from litestar import Litestar
from litestar.testing import AsyncTestClient
from sqlalchemy import select

from app.db import models as m
from app.lib.crypt import get_password_hash
from tests.factories import UserFactory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.integration, pytest.mark.security, pytest.mark.endpoints]


class TestInputValidation:
    """Test input validation across all endpoints."""

    async def _login_user(self, client: AsyncTestClient, user: m.User) -> str:
        """Helper to login user and return auth token."""
        response = await client.post(
            "/api/access/login",
            data={"username": user.email, "password": "testPassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_email_validation_registration(
        self,
        app: Litestar,
    ) -> None:
        """Test email validation in user registration."""
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@missinglocal.com",
            "spaces in@email.com",
            "double..dot@email.com",
            "toolong" + "x" * 250 + "@example.com",
        ]

        async with AsyncTestClient(app=app) as client:
            for invalid_email in invalid_emails:
                response = await client.post(
                    "/api/access/signup",
                    json={"email": invalid_email, "password": "securePassword123!", "name": "Test User"},
                )
                assert response.status_code == 422, f"Email {invalid_email} should be invalid"

    @pytest.mark.asyncio
    async def test_password_strength_validation(
        self,
        app: Litestar,
    ) -> None:
        """Test password strength validation."""
        weak_passwords = [
            "weak",  # Too short
            "password",  # No uppercase, numbers, symbols
            "PASSWORD",  # No lowercase, numbers, symbols
            "12345678",  # No letters
            "Password123",  # No symbols
            "p@ssw0rd",  # Too short with requirements
            "",  # Empty
            "   ",  # Whitespace only
        ]

        async with AsyncTestClient(app=app) as client:
            for weak_password in weak_passwords:
                response = await client.post(
                    "/api/access/signup",
                    json={"email": "test@example.com", "password": weak_password, "name": "Test User"},
                )
                assert response.status_code == 422, f"Password '{weak_password}' should be invalid"

    @pytest.mark.asyncio
    async def test_username_validation(
        self,
        app: Litestar,
    ) -> None:
        """Test username validation."""
        invalid_usernames = [
            "us",  # Too short
            "a" * 51,  # Too long
            "user name",  # Spaces
            "user@name",  # @ symbol
            "user.name.",  # Ending with dot
            ".username",  # Starting with dot
            "user..name",  # Double dots
            "123",  # Only numbers
            "user-",  # Ending with hyphen
            "-user",  # Starting with hyphen
        ]

        async with AsyncTestClient(app=app) as client:
            for invalid_username in invalid_usernames:
                response = await client.post(
                    "/api/access/signup",
                    json={
                        "email": "test@example.com",
                        "password": "securePassword123!",
                        "name": "Test User",
                        "username": invalid_username,
                    },
                )
                assert response.status_code == 422, f"Username '{invalid_username}' should be invalid"

    @pytest.mark.asyncio
    async def test_phone_validation(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test phone number validation."""
        # Create authenticated user for profile updates
        user = UserFactory.build(
            hashed_password=await get_password_hash("testPassword123!"), is_active=True, is_verified=True
        )
        session.add(user)
        await session.commit()

        invalid_phones = [
            "123",  # Too short
            "not-a-phone",  # Invalid format
            "123-456-789",  # Invalid format
            "+1 (555) 123",  # Incomplete
            "555-123-4567890",  # Too long
            "++1234567890",  # Double plus
        ]

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            for invalid_phone in invalid_phones:
                response = await client.patch(
                    "/api/me", json={"phone": invalid_phone}, headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code == 422, f"Phone '{invalid_phone}' should be invalid"

    @pytest.mark.asyncio
    async def test_name_validation(
        self,
        app: Litestar,
    ) -> None:
        """Test name validation."""
        invalid_names = [
            "",  # Empty
            "A",  # Too short
            "A" * 101,  # Too long
            "Name123",  # Contains numbers
            "Name@User",  # Contains symbols
            "   ",  # Whitespace only
            "Name  Name",  # Multiple consecutive spaces
        ]

        async with AsyncTestClient(app=app) as client:
            for invalid_name in invalid_names:
                response = await client.post(
                    "/api/access/signup",
                    json={"email": "test@example.com", "password": "securePassword123!", "name": invalid_name},
                )
                assert response.status_code == 422, f"Name '{invalid_name}' should be invalid"

    @pytest.mark.asyncio
    async def test_team_name_validation(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test team name validation."""
        user = UserFactory.build(
            hashed_password=await get_password_hash("testPassword123!"), is_active=True, is_verified=True
        )
        session.add(user)
        await session.commit()

        invalid_team_names = [
            "",  # Empty
            "A",  # Too short
            "A" * 101,  # Too long
            "   ",  # Whitespace only
        ]

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            for invalid_name in invalid_team_names:
                response = await client.post(
                    "/api/teams",
                    json={"name": invalid_name, "description": "Test team"},
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert response.status_code == 422, f"Team name '{invalid_name}' should be invalid"

    @pytest.mark.asyncio
    async def test_json_payload_validation(
        self,
        app: Litestar,
    ) -> None:
        """Test JSON payload validation."""
        async with AsyncTestClient(app=app) as client:
            # Invalid JSON
            response = await client.post(
                "/api/access/signup", content="not-json-data", headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 400

            # Missing required fields
            response = await client.post(
                "/api/access/signup",
                json={"email": "test@example.com"},  # Missing password
            )
            assert response.status_code == 422

            # Extra unexpected fields should be ignored or rejected
            response = await client.post(
                "/api/access/signup",
                json={
                    "email": "test@example.com",
                    "password": "securePassword123!",
                    "unexpected_field": "should_be_ignored",
                },
            )
            # Should succeed as msgspec typically ignores extra fields
            assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_url_parameter_validation(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test URL parameter validation."""
        user = UserFactory.build(
            hashed_password=await get_password_hash("testPassword123!"), is_active=True, is_verified=True
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            # Invalid UUID format
            response = await client.get("/api/teams/not-a-uuid", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 422

            # Valid UUID format but non-existent resource
            response = await client.get(f"/api/teams/{uuid4()}", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code in [403, 404]  # Could be either depending on permissions


class TestSQLInjectionProtection:
    """Test SQL injection protection across endpoints."""

    async def _login_user(self, client: AsyncTestClient, user: m.User) -> str:
        """Helper to login user and return auth token."""
        response = await client.post(
            "/api/access/login",
            data={"username": user.email, "password": "testPassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_sql_injection_in_login(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test SQL injection attempts in login endpoint."""
        # Create a valid user first
        user = UserFactory.build(
            email="valid@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        sql_injection_attempts = [
            "admin@example.com' OR '1'='1",
            "admin@example.com'; DROP TABLE user_account; --",
            "admin@example.com' UNION SELECT * FROM user_account --",
            "admin@example.com' OR 1=1 --",
            "admin'; EXEC master..xp_cmdshell 'ping google.com'--",
        ]

        async with AsyncTestClient(app=app) as client:
            for injection_attempt in sql_injection_attempts:
                response = await client.post(
                    "/api/access/login",
                    data={"username": injection_attempt, "password": "anyPassword"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                # Should fail authentication, not cause SQL error
                assert response.status_code in [401, 422], (
                    f"SQL injection attempt should be safely handled: {injection_attempt}"
                )

    @pytest.mark.asyncio
    async def test_sql_injection_in_search_fields(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test SQL injection attempts in search parameters."""
        user = UserFactory.build(
            email="searcher@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
            is_superuser=True,  # Need superuser to access user list
        )
        session.add(user)
        await session.commit()

        injection_attempts = [
            "'; DROP TABLE user_account; --",
            "' OR 1=1 --",
            "' UNION SELECT password FROM user_account --",
            "\\'; INSERT INTO user_account (email) VALUES ('hacked@example.com'); --",
        ]

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            for injection_attempt in injection_attempts:
                response = await client.get(
                    "/api/users", params={"search": injection_attempt}, headers={"Authorization": f"Bearer {token}"}
                )
                # Should return normal response, not SQL error
                assert response.status_code == 200, f"Search injection should be safely handled: {injection_attempt}"

    @pytest.mark.asyncio
    async def test_sql_injection_in_filters(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test SQL injection attempts in filter parameters."""
        user = UserFactory.build(
            hashed_password=await get_password_hash("testPassword123!"), is_active=True, is_verified=True
        )
        session.add(user)
        await session.commit()

        injection_attempts = [
            "'; DROP TABLE team; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM user_account WHERE '1'='1",
        ]

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            for injection_attempt in injection_attempts:
                response = await client.get(
                    "/api/teams", params={"id_filter": injection_attempt}, headers={"Authorization": f"Bearer {token}"}
                )
                # Should return validation error or empty results, not SQL error
                assert response.status_code in [200, 422], (
                    f"Filter injection should be safely handled: {injection_attempt}"
                )

    @pytest.mark.asyncio
    async def test_sql_injection_protection_verification(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Verify that SQL injection attempts don't affect database integrity."""
        # Create test data
        user = UserFactory.build(
            email="integrity@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        # Count users before injection attempts
        result = await session.execute(select(m.User))
        users_before = len(result.scalars().all())

        async with AsyncTestClient(app=app) as client:
            # Attempt various SQL injections
            await client.post(
                "/api/access/login",
                data={"username": "admin'; DROP TABLE user_account; --", "password": "anyPassword"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            await client.post(
                "/api/access/signup",
                json={
                    "email": "test'; INSERT INTO user_account (email) VALUES ('injected@example.com'); --@example.com",
                    "password": "securePassword123!",
                    "name": "Injection Attempt",
                },
            )

        # Verify database integrity is maintained
        result = await session.execute(select(m.User))
        users_after = len(result.scalars().all())

        # User count should not have changed due to injection attempts
        assert users_after == users_before, "Database should not be affected by SQL injection attempts"

        # Verify no malicious users were created
        result = await session.execute(select(m.User).where(m.User.email.like("%injected%")))
        injected_users = result.scalars().all()
        assert len(injected_users) == 0, "No users should be created via SQL injection"


class TestAuthenticationSecurity:
    """Test authentication and authorization security."""

    @pytest.mark.asyncio
    async def test_jwt_token_validation(
        self,
        app: Litestar,
    ) -> None:
        """Test JWT token validation and security."""
        async with AsyncTestClient(app=app) as client:
            # Test with invalid token format
            response = await client.get("/api/me", headers={"Authorization": "Bearer invalid-token"})
            assert response.status_code == 401

            # Test with malformed token
            response = await client.get("/api/me", headers={"Authorization": "Bearer not.a.jwt"})
            assert response.status_code == 401

            # Test with no token
            response = await client.get("/api/me")
            assert response.status_code == 401

            # Test with wrong auth scheme
            response = await client.get("/api/me", headers={"Authorization": "Basic dGVzdDp0ZXN0"})
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_session_security(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test session security features."""
        user = UserFactory.build(
            email="session@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # Login to get a valid token
            response = await client.post(
                "/api/access/login",
                data={"username": "session@example.com", "password": "testPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 200
            token = response.json()["access_token"]

            # Use token to access protected resource
            response = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200

            # Logout should invalidate session
            response = await client.post("/api/access/logout")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limiting_protection(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test rate limiting for security-sensitive endpoints."""
        user = UserFactory.build(email="ratelimit@example.com", is_active=True, is_verified=True)
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # Test rate limiting on password reset
            for _ in range(3):  # Should be allowed
                response = await client.post("/api/access/forgot-password", json={"email": "ratelimit@example.com"})
                assert response.status_code == 200

            # Fourth request should be rate limited
            response = await client.post("/api/access/forgot-password", json={"email": "ratelimit@example.com"})
            assert response.status_code == 200  # Still returns 200 for security
            response_data = response.json()
            assert "Too many" in response_data["message"]

    @pytest.mark.asyncio
    async def test_password_security_features(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test password security features."""
        user = UserFactory.build(
            email="password@example.com",
            hashed_password=await get_password_hash("oldPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # Login with current password
            response = await client.post(
                "/api/access/login",
                data={"username": "password@example.com", "password": "oldPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 200
            token = response.json()["access_token"]

            # Test password reuse prevention could be implemented here
            # Test password complexity requirements
            response = await client.patch(
                "/api/me/password",
                json={
                    "currentPassword": "oldPassword123!",
                    "newPassword": "weak",  # Should fail validation
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 422


class TestDataSanitization:
    """Test data sanitization and output security."""

    async def _login_user(self, client: AsyncTestClient, user: m.User) -> str:
        """Helper to login user and return auth token."""
        response = await client.post(
            "/api/access/login",
            data={"username": user.email, "password": "testPassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_xss_prevention_in_names(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test XSS prevention in user and team names."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ]

        user = UserFactory.build(
            hashed_password=await get_password_hash("testPassword123!"), is_active=True, is_verified=True
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            for xss_payload in xss_payloads:
                # Test in profile update
                response = await client.patch(
                    "/api/me", json={"name": xss_payload}, headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 200:
                    # If accepted, verify it's properly sanitized in response
                    response_data = response.json()
                    assert "<script>" not in response_data.get("name", "")
                    assert "javascript:" not in response_data.get("name", "")
                else:
                    # Should be rejected with validation error
                    assert response.status_code == 422

                # Test in team creation
                response = await client.post(
                    "/api/teams",
                    json={"name": xss_payload, "description": "Test team"},
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code == 201:
                    response_data = response.json()
                    assert "<script>" not in response_data.get("name", "")
                    assert "javascript:" not in response_data.get("name", "")
                else:
                    assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_sensitive_data_exposure(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test that sensitive data is not exposed in responses."""
        user = UserFactory.build(
            email="sensitive@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            token = await self._login_user(client, user)

            # Get user profile
            response = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200

            response_data = response.json()
            response_text = response.text.lower()

            # Verify sensitive fields are not exposed
            assert "password" not in response_data
            assert "hashed_password" not in response_data
            assert "hashedpassword" not in response_text
            assert "secret" not in response_text
            assert "token" not in response_data or "hasPassword" in response_data  # Only metadata allowed

    @pytest.mark.asyncio
    async def test_error_message_security(
        self,
        app: Litestar,
    ) -> None:
        """Test that error messages don't leak sensitive information."""
        async with AsyncTestClient(app=app) as client:
            # Test login with non-existent user
            response = await client.post(
                "/api/access/login",
                data={"username": "nonexistent@example.com", "password": "anyPassword"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            assert response.status_code == 401
            # Error message should not reveal whether user exists
            error_text = response.text.lower()
            assert "not found" not in error_text
            assert "does not exist" not in error_text
            assert "invalid credentials" in error_text or "unauthorized" in error_text

            # Test password reset for non-existent user
            response = await client.post("/api/access/forgot-password", json={"email": "nonexistent@example.com"})

            # Should return success message for security (timing attack prevention)
            assert response.status_code == 200
            response_data = response.json()
            assert "if the email exists" in response_data["message"].lower()


class TestAccessControl:
    """Test access control and authorization."""

    async def _login_user(self, client: AsyncTestClient, user: m.User) -> str:
        """Helper to login user and return auth token."""
        response = await client.post(
            "/api/access/login",
            data={"username": user.email, "password": "testPassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_unauthorized_access_prevention(
        self,
        app: Litestar,
    ) -> None:
        """Test that unauthorized access is properly prevented."""
        protected_endpoints = [
            ("GET", "/api/me"),
            ("PATCH", "/api/me"),
            ("PATCH", "/api/me/password"),
            ("GET", "/api/teams"),
            ("POST", "/api/teams"),
        ]

        async with AsyncTestClient(app=app) as client:
            for method, endpoint in protected_endpoints:
                if method == "GET":
                    response = await client.get(endpoint)
                elif method == "POST":
                    response = await client.post(endpoint, json={})
                elif method == "PATCH":
                    response = await client.patch(endpoint, json={})

                assert response.status_code == 401, f"{method} {endpoint} should require authentication"

    @pytest.mark.asyncio
    async def test_inactive_user_access_denial(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test that inactive users cannot access protected resources."""
        inactive_user = UserFactory.build(
            email="inactive@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=False,  # Inactive user
            is_verified=True,
        )
        session.add(inactive_user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # Should not be able to login
            response = await client.post(
                "/api/access/login",
                data={"username": "inactive@example.com", "password": "testPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unverified_user_access_denial(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test that unverified users cannot access protected resources."""
        unverified_user = UserFactory.build(
            email="unverified@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=False,  # Unverified user
        )
        session.add(unverified_user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # Should not be able to login
            response = await client.post(
                "/api/access/login",
                data={"username": "unverified@example.com", "password": "testPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_superuser_access_control(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test superuser-only endpoint access control."""
        # Create regular user
        regular_user = UserFactory.build(
            email="regular@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )

        # Create superuser
        super_user = UserFactory.build(
            email="super@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
            is_superuser=True,
        )

        session.add_all([regular_user, super_user])
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # Regular user should not access superuser endpoints
            regular_token = await self._login_user(client, regular_user)
            response = await client.get(
                "/api/users",  # Superuser-only endpoint
                headers={"Authorization": f"Bearer {regular_token}"},
            )
            assert response.status_code == 403

            # Superuser should access superuser endpoints
            super_token = await self._login_user(client, super_user)
            response = await client.get("/api/users", headers={"Authorization": f"Bearer {super_token}"})
            assert response.status_code == 200


class TestSecurityHeaders:
    """Test security headers and response security."""

    @pytest.mark.asyncio
    async def test_security_headers_present(
        self,
        app: Litestar,
    ) -> None:
        """Test that important security headers are present."""
        async with AsyncTestClient(app=app) as client:
            response = await client.get("/api/access/logout")

            # Check for security headers (may vary based on Litestar configuration)
            headers = response.headers

            # These headers help prevent various attacks
            security_header_checks = [
                # Content type should be properly set
                lambda h: "content-type" in h,
                # CORS headers should be controlled
                lambda h: "access-control-allow-origin" not in h or h["access-control-allow-origin"] != "*",
            ]

            for check in security_header_checks:
                assert check(headers), f"Security header check failed for headers: {dict(headers)}"

    @pytest.mark.asyncio
    async def test_content_type_security(
        self,
        app: Litestar,
    ) -> None:
        """Test content type security."""
        async with AsyncTestClient(app=app) as client:
            response = await client.post(
                "/api/access/signup",
                json={"email": "test@example.com", "password": "securePassword123!", "name": "Test User"},
            )

            # Response should have proper content type
            assert "application/json" in response.headers.get("content-type", "").lower()

    @pytest.mark.asyncio
    async def test_response_data_consistency(
        self,
        app: Litestar,
        session: AsyncSession,
    ) -> None:
        """Test that response data is consistent and secure."""
        user = UserFactory.build(
            email="consistent@example.com",
            hashed_password=await get_password_hash("testPassword123!"),
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()

        async with AsyncTestClient(app=app) as client:
            # Login
            response = await client.post(
                "/api/access/login",
                data={"username": "consistent@example.com", "password": "testPassword123!"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            assert response.status_code == 200

            login_data = response.json()
            assert "access_token" in login_data
            assert "token_type" in login_data
            assert login_data["token_type"] == "Bearer"

            # Profile response should be consistent
            token = login_data["access_token"]
            response = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200

            profile_data = response.json()
            assert profile_data["email"] == "consistent@example.com"
            assert "id" in profile_data
            assert isinstance(profile_data["isActive"], bool)
            assert isinstance(profile_data["isVerified"], bool)
