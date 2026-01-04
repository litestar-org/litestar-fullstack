import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    ("username", "password", "expected_status_code"),
    (
        ("superuser@example1.com", "Test_Password1!", 403),
        ("superuser@example.com", "Test_Password1!", 201),
        ("user@example.com", "Test_Password1!", 403),
        ("user@example.com", "Test_Password2!", 201),
        ("inactive@example.com", "Old_Password2!", 403),
        ("inactive@example.com", "Old_Password3!", 403),
    ),
)
async def test_user_login(seeded_client: AsyncClient, username: str, password: str, expected_status_code: int) -> None:
    response = await seeded_client.post("/api/access/login", data={"username": username, "password": password})
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    ("username", "password"),
    (("superuser@example.com", "Test_Password1!"),),
)
async def test_user_logout(seeded_client: AsyncClient, username: str, password: str) -> None:
    response = await seeded_client.post("/api/access/login", data={"username": username, "password": password})
    assert response.status_code == 201
    cookies = dict(response.cookies)

    assert cookies.get("token") is not None

    me_response = await seeded_client.get("/api/me")
    assert me_response.status_code == 200

    response = await seeded_client.post("/api/access/logout")
    assert response.status_code == 200

    # the user can no longer access the /me route.
    me_response = await seeded_client.get("/api/me")
    assert me_response.status_code == 401
