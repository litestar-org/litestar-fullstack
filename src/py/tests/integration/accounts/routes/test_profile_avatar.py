"""Integration tests for profile avatar endpoints."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


# Minimal valid PNG file (1x1 transparent pixel) for upload tests
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
)


async def test_upload_avatar_no_auth(client: "AsyncClient") -> None:
    """Unauthenticated upload requests are rejected."""
    response = await client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 401


async def test_get_avatar_no_auth(client: "AsyncClient") -> None:
    """Unauthenticated get requests are rejected."""
    response = await client.get("/api/me/avatar")
    assert response.status_code == 401


async def test_delete_avatar_no_auth(client: "AsyncClient") -> None:
    """Unauthenticated delete requests are rejected."""
    response = await client.delete("/api/me/avatar")
    assert response.status_code == 401


async def test_upload_avatar_success(authenticated_client: "AsyncClient") -> None:
    """A valid PNG upload succeeds and returns the updated profile."""
    response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["avatarUrl"] == "/api/me/avatar"


async def test_upload_avatar_invalid_content_type(authenticated_client: "AsyncClient") -> None:
    """Uploads with a non-image content type are rejected."""
    response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


async def test_upload_avatar_too_large(authenticated_client: "AsyncClient") -> None:
    """Uploads larger than 5MB are rejected."""
    # 5MB + 1 byte of zeros, with PNG content-type to pass the type check
    large_data = b"\x00" * (5 * 1024 * 1024 + 1)
    response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("big.png", large_data, "image/png")},
    )
    assert response.status_code == 400


async def test_get_avatar_not_set(authenticated_client: "AsyncClient") -> None:
    """GET returns 404 when the user has no avatar."""
    response = await authenticated_client.get("/api/me/avatar")
    assert response.status_code == 404


async def test_get_avatar_after_upload(authenticated_client: "AsyncClient") -> None:
    """GET returns the uploaded bytes with the correct content type."""
    upload_response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert upload_response.status_code == 201

    response = await authenticated_client.get("/api/me/avatar")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.content == PNG_BYTES


async def test_delete_avatar_not_set(authenticated_client: "AsyncClient") -> None:
    """DELETE returns 404 when the user has no avatar."""
    response = await authenticated_client.delete("/api/me/avatar")
    assert response.status_code == 404


async def test_delete_avatar_success(authenticated_client: "AsyncClient") -> None:
    """DELETE removes an existing avatar and subsequent GET returns 404."""
    upload_response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert upload_response.status_code == 201

    delete_response = await authenticated_client.delete("/api/me/avatar")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Avatar removed successfully."

    # Verify avatar is gone
    get_response = await authenticated_client.get("/api/me/avatar")
    assert get_response.status_code == 404


async def test_profile_includes_avatar_url_after_upload(authenticated_client: "AsyncClient") -> None:
    """The /api/me profile response includes avatarUrl after upload."""
    # Before upload
    before = await authenticated_client.get("/api/me")
    assert before.status_code == 200
    assert before.json()["avatarUrl"] is None

    # After upload
    upload_response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert upload_response.status_code == 201

    after = await authenticated_client.get("/api/me")
    assert after.status_code == 200
    assert after.json()["avatarUrl"] == "/api/me/avatar"
