"""Integration tests for profile avatar endpoints."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


SUPERUSER_ID = "97108ac1-ffcb-411d-8b1e-d9183399f63b"
USER_ID = "5ef29f3c-3560-4d15-ba6b-a2e5c721e4d2"
AVATAR_URL_RE = re.compile(r"^/api/users/[0-9a-f-]{36}/avatar\?v=[0-9a-f]{32}$")

# Minimal valid PNG file (1x1 transparent pixel) for upload tests
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
)


async def test_upload_avatar_no_auth(client: AsyncClient) -> None:
    """Unauthenticated upload requests are rejected."""
    response = await client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 401


async def test_get_avatar_no_auth(client: AsyncClient) -> None:
    """Unauthenticated get requests are rejected."""
    response = await client.get("/api/me/avatar")
    assert response.status_code == 401


async def test_delete_avatar_no_auth(client: AsyncClient) -> None:
    """Unauthenticated delete requests are rejected."""
    response = await client.delete("/api/me/avatar")
    assert response.status_code == 401


async def test_upload_avatar_success(authenticated_client: AsyncClient) -> None:
    """A valid PNG upload succeeds and returns the updated profile."""
    response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert AVATAR_URL_RE.match(body["avatarUrl"])
    assert body["avatarUrl"].startswith(f"/api/users/{body['id']}/avatar")


async def test_upload_avatar_replacement_changes_url(authenticated_client: AsyncClient) -> None:
    """Each upload yields a new avatarUrl so browsers never show a cached image."""
    urls = set()
    for _ in range(2):
        response = await authenticated_client.post(
            "/api/me/avatar",
            files={"data": ("avatar.png", PNG_BYTES, "image/png")},
        )
        assert response.status_code == 201
        urls.add(response.json()["avatarUrl"])
    assert len(urls) == 2


async def test_upload_avatar_just_under_limit_reaches_service(authenticated_client: AsyncClient) -> None:
    """A file at the size cap is not rejected by the multipart body limit."""
    data = PNG_BYTES + b"\x00" * (5 * 1024 * 1024 - len(PNG_BYTES))
    response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", data, "image/png")},
    )
    assert response.status_code == 201


async def test_upload_avatar_invalid_content_type(authenticated_client: AsyncClient) -> None:
    """Uploads with a non-image content type are rejected."""
    response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


async def test_upload_avatar_too_large(authenticated_client: AsyncClient) -> None:
    """Uploads larger than 5MB are rejected by the service size check."""
    # A valid PNG header padded to 5MB + 1 byte — within the request body cap
    # (which leaves room for multipart overhead) but over the file limit.
    large_data = PNG_BYTES + b"\x00" * (5 * 1024 * 1024 + 1 - len(PNG_BYTES))
    response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("big.png", large_data, "image/png")},
    )
    assert response.status_code == 413


async def test_upload_avatar_over_request_body_cap(authenticated_client: AsyncClient) -> None:
    """Bodies far beyond the cap are rejected before being read in full."""
    response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("big.png", b"\x00" * (6 * 1024 * 1024), "image/png")},
    )
    assert response.status_code == 413


async def test_get_avatar_not_set(authenticated_client: AsyncClient) -> None:
    """GET returns 404 when the user has no avatar."""
    response = await authenticated_client.get("/api/me/avatar")
    assert response.status_code == 404


async def test_get_avatar_after_upload(authenticated_client: AsyncClient) -> None:
    """GET returns the uploaded bytes with the correct content type."""
    upload_response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert upload_response.status_code == 201

    response = await authenticated_client.get("/api/me/avatar")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.headers["cache-control"] == "private, no-cache"
    assert response.content == PNG_BYTES

    by_id = await authenticated_client.get(upload_response.json()["avatarUrl"])
    assert by_id.status_code == 200
    assert by_id.content == PNG_BYTES


async def test_get_avatar_missing_object_returns_404(authenticated_client: AsyncClient) -> None:
    """A row whose stored object has vanished yields 404, not 500."""
    from advanced_alchemy.types.file_object import storages

    from app.lib.settings import StorageSettings

    upload_response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert upload_response.status_code == 201

    store = storages.get_backend(StorageSettings.BACKEND_KEY).fs
    async for batch in store.list_async():
        for entry in batch:
            await store.delete_async(entry["path"])

    response = await authenticated_client.get("/api/me/avatar")
    assert response.status_code == 404


async def test_user_avatar_access_is_limited_to_self_and_superusers(
    seeded_client: AsyncClient,
    superuser_token_headers: dict[str, str],
    user_token_headers: dict[str, str],
) -> None:
    """Superusers can view any avatar; regular users only their own."""
    for headers in (superuser_token_headers, user_token_headers):
        response = await seeded_client.post(
            "/api/me/avatar",
            files={"data": ("avatar.png", PNG_BYTES, "image/png")},
            headers=headers,
        )
        assert response.status_code == 201

    as_superuser = await seeded_client.get(f"/api/users/{USER_ID}/avatar", headers=superuser_token_headers)
    assert as_superuser.status_code == 200
    assert as_superuser.content == PNG_BYTES

    as_user = await seeded_client.get(f"/api/users/{SUPERUSER_ID}/avatar", headers=user_token_headers)
    assert as_user.status_code == 404

    own = await seeded_client.get(f"/api/users/{USER_ID}/avatar", headers=user_token_headers)
    assert own.status_code == 200


async def test_delete_avatar_not_set(authenticated_client: AsyncClient) -> None:
    """DELETE returns 404 when the user has no avatar."""
    response = await authenticated_client.delete("/api/me/avatar")
    assert response.status_code == 404


async def test_delete_avatar_success(authenticated_client: AsyncClient) -> None:
    """DELETE removes an existing avatar and subsequent GET returns 404."""
    upload_response = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert upload_response.status_code == 201

    delete_response = await authenticated_client.delete("/api/me/avatar")
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    # Verify avatar is gone
    get_response = await authenticated_client.get("/api/me/avatar")
    assert get_response.status_code == 404


async def test_upload_avatar_replacement_cleans_up_old_object(authenticated_client: AsyncClient) -> None:
    """Replacing an existing avatar removes the previous file from storage.

    Verifies the advanced-alchemy session tracker actually deletes the prior
    object when ``User.avatar`` is reassigned.
    """
    from advanced_alchemy.types.file_object import storages

    from app.lib.settings import StorageSettings

    backend = storages.get_backend(StorageSettings.BACKEND_KEY)
    store = backend.fs  # MemoryStore in tests

    async def _list_keys() -> set[str]:
        keys: set[str] = set()
        list_stream = store.list_async()
        async for batch in list_stream:
            for entry in batch:
                keys.add(entry["path"])
        return keys

    # The in-memory store is session-scoped, so ignore objects left by other tests.
    keys_before = await _list_keys()

    # First upload — capture stored key(s)
    first = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar.png", PNG_BYTES, "image/png")},
    )
    assert first.status_code == 201
    keys_after_first = await _list_keys() - keys_before
    assert keys_after_first, "First upload did not produce any stored object"

    # Second upload — old object should be cleaned up
    second = await authenticated_client.post(
        "/api/me/avatar",
        files={"data": ("avatar2.png", PNG_BYTES, "image/png")},
    )
    assert second.status_code == 201
    keys_after_second = await _list_keys()

    survivors = keys_after_first & keys_after_second
    assert not survivors, f"Replaced avatar object(s) not cleaned up: {survivors}"


async def test_profile_includes_avatar_url_after_upload(authenticated_client: AsyncClient) -> None:
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
    assert after.json()["avatarUrl"] == upload_response.json()["avatarUrl"]
