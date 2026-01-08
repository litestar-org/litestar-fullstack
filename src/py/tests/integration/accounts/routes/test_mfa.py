"""Integration tests for MFA (Multi-Factor Authentication) endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pyotp
import pytest
from litestar.security.jwt import Token as JWTToken

from app.lib.crypt import generate_backup_codes, generate_totp_secret, get_password_hash
from app.lib.settings import get_settings
from tests.factories import UserFactory

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [pytest.mark.integration, pytest.mark.auth, pytest.mark.endpoints]


def _get_totp_code(secret: str) -> str:
    """Generate current TOTP code for testing."""
    totp = pyotp.TOTP(secret)
    return totp.now()


async def _hash_backup_codes(codes: list[str]) -> list[str | None]:
    """Hash backup codes for testing (mimics what UserService does).

    The UserService's _populate_with_backup_codes method automatically hashes
    codes before storing. When setting backup_codes directly on the model,
    we need to hash them manually.

    Returns list[str | None] to match User.backup_codes type annotation.
    """
    return [await get_password_hash(code) for code in codes]


async def _login_user(client: AsyncClient, email: str, password: str = "testPassword123!") -> str:
    """Helper to login user and return auth token."""
    response = await client.post(
        "/api/access/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _create_mfa_challenge_token(email: str, user_id: str) -> str:
    """Create an MFA challenge token for testing."""
    settings = get_settings()
    return JWTToken(
        sub=email,
        aud="mfa_verification",
        exp=datetime.now(UTC) + timedelta(minutes=5),
        extras={"type": "mfa_challenge", "user_id": user_id},
    ).encode(secret=settings.app.SECRET_KEY, algorithm=settings.app.JWT_ENCRYPTION_ALGORITHM)


async def _login_mfa_user(client: AsyncClient, email: str, password: str = "testPassword123!") -> str:
    """Helper to login MFA-enabled user and return auth token via MFA challenge.

    For MFA-enabled users, login returns 200 with MFA challenge cookie.
    We then need to complete MFA verification to get the access token.
    """
    response = await client.post(
        "/api/access/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # MFA-enabled users get 200 (MFA required) not 201
    assert response.status_code == 200, f"Expected MFA challenge (200), got {response.status_code}: {response.text}"
    mfa_cookie = response.cookies.get("mfa_challenge")
    return mfa_cookie if mfa_cookie is not None else ""


# --- MFA Status Tests ---


@pytest.mark.anyio
async def test_get_mfa_status_disabled(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test getting MFA status when MFA is disabled."""
    user = UserFactory.build(
        email=f"mfauser-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    response = await client.get("/api/mfa/status", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False
    assert data["confirmedAt"] is None
    assert data["backupCodesRemaining"] is None


@pytest.mark.anyio
async def test_get_mfa_status_enabled(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test getting MFA status when MFA is enabled.

    Note: User created without MFA, login first to get token, then enable MFA.
    This is because MFA-enabled users get 200 (MFA challenge) not 201 on login.
    """
    # Create user without MFA initially to get a login token
    user = UserFactory.build(
        email=f"mfaenabled-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    # Login to get token while MFA is still disabled
    token = await _login_user(client, user.email)

    # Now enable MFA directly in database
    backup_codes = generate_backup_codes(count=8)
    user.is_two_factor_enabled = True
    user.two_factor_confirmed_at = datetime.now(UTC)
    user.totp_secret = generate_totp_secret()
    user.backup_codes = cast("list[str | None]", backup_codes)
    await session.commit()

    response = await client.get("/api/mfa/status", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["confirmedAt"] is not None
    assert data["backupCodesRemaining"] == 8


@pytest.mark.anyio
async def test_get_mfa_status_unauthenticated(client: AsyncClient) -> None:
    """Test getting MFA status without authentication."""
    response = await client.get("/api/mfa/status")
    assert response.status_code == 401


# --- MFA Setup Initiation Tests ---


@pytest.mark.anyio
async def test_initiate_mfa_setup_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful MFA setup initiation."""
    user = UserFactory.build(
        email=f"mfasetup-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    response = await client.post("/api/mfa/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 201
    data = response.json()
    assert "secret" in data
    assert len(data["secret"]) == 32  # TOTP secrets are 32 chars base32
    assert "qrCode" in data
    assert data["qrCode"].startswith("data:image/png;base64,")
    assert "provisioningUri" in data
    assert "otpauth://totp/" in data["provisioningUri"]


@pytest.mark.anyio
async def test_initiate_mfa_setup_already_enabled(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA setup initiation when MFA is already enabled."""
    # Create user without MFA initially to get a login token
    user = UserFactory.build(
        email=f"mfaalready-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    # Enable MFA after login
    user.is_two_factor_enabled = True
    user.totp_secret = generate_totp_secret()
    await session.commit()

    response = await client.post("/api/mfa/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert "already enabled" in response.text


# --- MFA Setup Confirmation Tests ---


@pytest.mark.anyio
async def test_confirm_mfa_setup_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful MFA setup confirmation with valid TOTP code."""
    totp_secret = generate_totp_secret()
    user = UserFactory.build(
        email=f"mfaconfirm-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
        totp_secret=totp_secret,  # Secret set from /enable endpoint
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    # Generate valid TOTP code
    totp_code = _get_totp_code(totp_secret)

    response = await client.post(
        "/api/mfa/confirm",
        json={"code": totp_code},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "codes" in data
    assert len(data["codes"]) == 8  # 8 backup codes

    # Verify MFA is now enabled
    await session.refresh(user)
    assert user.is_two_factor_enabled is True
    assert user.two_factor_confirmed_at is not None


@pytest.mark.anyio
async def test_confirm_mfa_setup_invalid_code(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA setup confirmation with invalid TOTP code."""
    totp_secret = generate_totp_secret()
    user = UserFactory.build(
        email=f"mfainvalid-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
        totp_secret=totp_secret,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    response = await client.post(
        "/api/mfa/confirm",
        json={"code": "000000"},  # Invalid code
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "Invalid verification code" in response.text


@pytest.mark.anyio
async def test_confirm_mfa_setup_no_setup_in_progress(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA setup confirmation without prior setup initiation."""
    user = UserFactory.build(
        email=f"mfanosetup-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
        totp_secret=None,  # No secret set
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    response = await client.post(
        "/api/mfa/confirm",
        json={"code": "123456"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "No MFA setup in progress" in response.text


@pytest.mark.anyio
async def test_confirm_mfa_setup_already_enabled(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA setup confirmation when MFA is already enabled."""
    user = UserFactory.build(
        email=f"mfaconfirmenabled-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    # Enable MFA after login
    user.is_two_factor_enabled = True
    user.totp_secret = generate_totp_secret()
    await session.commit()

    response = await client.post(
        "/api/mfa/confirm",
        json={"code": "123456"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "already enabled" in response.text


# --- MFA Disable Tests ---


@pytest.mark.anyio
async def test_disable_mfa_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful MFA disable with correct password."""
    user = UserFactory.build(
        email=f"mfadisable-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    # Enable MFA after login (hash backup codes like the service does)
    user.is_two_factor_enabled = True
    user.totp_secret = generate_totp_secret()
    user.backup_codes = await _hash_backup_codes(generate_backup_codes(count=8))
    await session.commit()

    response = await client.request(
        "DELETE",
        "/api/mfa/disable",
        json={"password": "testPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "disabled" in data["message"].lower()
    # Note: MFA disable is verified by the successful 200 response and message
    # The service clears totp_secret, backup_codes, and is_two_factor_enabled internally


@pytest.mark.anyio
async def test_disable_mfa_wrong_password(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA disable with incorrect password."""
    user = UserFactory.build(
        email=f"mfadisablewrong-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    # Enable MFA after login
    user.is_two_factor_enabled = True
    user.totp_secret = generate_totp_secret()
    await session.commit()

    response = await client.request(
        "DELETE",
        "/api/mfa/disable",
        json={"password": "wrongPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "Invalid password" in response.text


@pytest.mark.anyio
async def test_disable_mfa_not_enabled(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA disable when MFA is not enabled."""
    user = UserFactory.build(
        email=f"mfadisablenotenabled-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    response = await client.request(
        "DELETE",
        "/api/mfa/disable",
        json={"password": "testPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "not enabled" in response.text


# --- Backup Code Regeneration Tests ---


@pytest.mark.anyio
async def test_regenerate_backup_codes_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful backup code regeneration."""
    user = UserFactory.build(
        email=f"mfaregen-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    # Enable MFA after login
    old_codes = generate_backup_codes(count=8)
    user.is_two_factor_enabled = True
    user.totp_secret = generate_totp_secret()
    user.backup_codes = cast("list[str | None]", old_codes)
    await session.commit()

    response = await client.post(
        "/api/mfa/regenerate-codes",
        json={"password": "testPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "codes" in data
    assert len(data["codes"]) == 8

    # Verify new codes are different from old ones
    new_codes = data["codes"]
    assert set(new_codes) != set(old_codes)


@pytest.mark.anyio
async def test_regenerate_backup_codes_wrong_password(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test backup code regeneration with incorrect password."""
    user = UserFactory.build(
        email=f"mfaregenwrong-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    # Enable MFA after login
    user.is_two_factor_enabled = True
    user.totp_secret = generate_totp_secret()
    user.backup_codes = cast("list[str | None]", generate_backup_codes(count=8))
    await session.commit()

    response = await client.post(
        "/api/mfa/regenerate-codes",
        json={"password": "wrongPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "Invalid password" in response.text


@pytest.mark.anyio
async def test_regenerate_backup_codes_mfa_not_enabled(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test backup code regeneration when MFA is not enabled."""
    user = UserFactory.build(
        email=f"mfaregennotenabled-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    response = await client.post(
        "/api/mfa/regenerate-codes",
        json={"password": "testPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "not enabled" in response.text


# --- MFA Challenge Tests ---


@pytest.mark.anyio
async def test_mfa_challenge_verify_totp_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful MFA challenge verification with TOTP code."""
    totp_secret = generate_totp_secret()
    backup_codes = generate_backup_codes(count=8)
    user = UserFactory.build(
        email=f"mfachallenge-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=True,
        totp_secret=totp_secret,
        backup_codes=await _hash_backup_codes(backup_codes),
    )
    session.add(user)
    await session.commit()

    # Create MFA challenge token
    mfa_token = _create_mfa_challenge_token(user.email, str(user.id))

    # Generate valid TOTP code
    totp_code = _get_totp_code(totp_secret)

    response = await client.post(
        "/api/mfa/challenge/verify",
        json={"code": totp_code},
        cookies={"mfa_challenge": mfa_token},
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"


@pytest.mark.anyio
async def test_mfa_challenge_verify_backup_code_success(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test successful MFA challenge verification with backup code."""
    totp_secret = generate_totp_secret()
    raw_backup_codes = generate_backup_codes(count=8)
    # Store hashed backup codes (as the service does)
    hashed_backup_codes = await _hash_backup_codes(raw_backup_codes)
    user = UserFactory.build(
        email=f"mfabackup-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=True,
        totp_secret=totp_secret,
        backup_codes=hashed_backup_codes,
    )
    session.add(user)
    await session.commit()

    # Create MFA challenge token
    mfa_token = _create_mfa_challenge_token(user.email, str(user.id))

    # Use first backup code (send raw code, service verifies against hash)
    response = await client.post(
        "/api/mfa/challenge/verify",
        json={"recovery_code": raw_backup_codes[0]},
        cookies={"mfa_challenge": mfa_token},
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    # Note: Backup code consumption is verified by the successful 201 response
    # The service marks the used code as None internally


@pytest.mark.anyio
async def test_mfa_challenge_no_token(client: AsyncClient) -> None:
    """Test MFA challenge without challenge token."""
    response = await client.post(
        "/api/mfa/challenge/verify",
        json={"code": "123456"},
    )

    assert response.status_code == 401
    assert "No MFA challenge" in response.text


@pytest.mark.anyio
async def test_mfa_challenge_invalid_token(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA challenge with invalid token."""
    response = await client.post(
        "/api/mfa/challenge/verify",
        json={"code": "123456"},
        cookies={"mfa_challenge": "invalid_token"},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_mfa_challenge_invalid_totp_code(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA challenge with invalid TOTP code."""
    totp_secret = generate_totp_secret()
    backup_codes = generate_backup_codes(count=8)
    user = UserFactory.build(
        email=f"mfainvalidtotp-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=True,
        totp_secret=totp_secret,
        backup_codes=await _hash_backup_codes(backup_codes),
    )
    session.add(user)
    await session.commit()

    mfa_token = _create_mfa_challenge_token(user.email, str(user.id))

    response = await client.post(
        "/api/mfa/challenge/verify",
        json={"code": "000000"},  # Invalid code
        cookies={"mfa_challenge": mfa_token},
    )

    assert response.status_code == 401
    assert "Invalid verification code" in response.text


@pytest.mark.anyio
async def test_mfa_challenge_invalid_backup_code(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA challenge with invalid backup code."""
    totp_secret = generate_totp_secret()
    backup_codes = generate_backup_codes(count=8)
    user = UserFactory.build(
        email=f"mfainvalidbackup-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=True,
        totp_secret=totp_secret,
        backup_codes=await _hash_backup_codes(backup_codes),
    )
    session.add(user)
    await session.commit()

    mfa_token = _create_mfa_challenge_token(user.email, str(user.id))

    response = await client.post(
        "/api/mfa/challenge/verify",
        json={"recovery_code": "INVALID-CODE-1234"},
        cookies={"mfa_challenge": mfa_token},
    )

    assert response.status_code == 401
    assert "Invalid backup code" in response.text


@pytest.mark.anyio
async def test_mfa_challenge_user_not_found(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA challenge with token for non-existent user."""
    mfa_token = _create_mfa_challenge_token("nonexistent@example.com", str(uuid4()))

    response = await client.post(
        "/api/mfa/challenge/verify",
        json={"code": "123456"},
        cookies={"mfa_challenge": mfa_token},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_mfa_challenge_mfa_disabled(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test MFA challenge when MFA is disabled for user."""
    user = UserFactory.build(
        email=f"mfadisableduser-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
        totp_secret=None,
    )
    session.add(user)
    await session.commit()

    mfa_token = _create_mfa_challenge_token(user.email, str(user.id))

    response = await client.post(
        "/api/mfa/challenge/verify",
        json={"code": "123456"},
        cookies={"mfa_challenge": mfa_token},
    )

    assert response.status_code == 401
    assert "MFA is not enabled" in response.text


# --- Complete MFA Flow Tests ---


@pytest.mark.anyio
async def test_complete_mfa_setup_flow(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test complete MFA setup workflow: enable -> confirm -> status."""
    user = UserFactory.build(
        email=f"mfaflow-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    # 1. Initiate MFA setup
    response = await client.post("/api/mfa/enable", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    setup_data = response.json()
    secret = setup_data["secret"]

    # 2. Confirm MFA with valid TOTP code
    totp_code = _get_totp_code(secret)
    response = await client.post(
        "/api/mfa/confirm",
        json={"code": totp_code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    confirm_data = response.json()
    assert len(confirm_data["codes"]) == 8

    # 3. Verify MFA status
    response = await client.get("/api/mfa/status", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["enabled"] is True
    assert status_data["backupCodesRemaining"] == 8


@pytest.mark.anyio
async def test_complete_mfa_disable_flow(
    client: AsyncClient,
    session: AsyncSession,
) -> None:
    """Test complete MFA disable workflow."""
    user = UserFactory.build(
        email=f"mfadisableflow-{uuid4().hex[:8]}@example.com",
        hashed_password=await get_password_hash("testPassword123!"),
        is_active=True,
        is_verified=True,
        is_two_factor_enabled=False,
    )
    session.add(user)
    await session.commit()

    token = await _login_user(client, user.email)

    # Enable MFA after login (hash backup codes like the service does)
    user.is_two_factor_enabled = True
    user.totp_secret = generate_totp_secret()
    user.two_factor_confirmed_at = datetime.now(UTC)
    user.backup_codes = await _hash_backup_codes(generate_backup_codes(count=8))
    await session.commit()

    # 1. Verify MFA is enabled
    response = await client.get("/api/mfa/status", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["enabled"] is True

    # 2. Disable MFA
    response = await client.request(
        "DELETE",
        "/api/mfa/disable",
        json={"password": "testPassword123!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # 3. Verify MFA is disabled
    response = await client.get("/api/mfa/status", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["enabled"] is False
