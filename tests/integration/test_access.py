from httpx import AsyncClient


async def test_user_login_valid(client: AsyncClient) -> None:
    response = await client.post(
        "/api/access/login", data={"username": "superuser@example.com", "password": "Test_Password1!"}
    )
    assert response.status_code == 201
    assert "access_token" in response.json()


async def test_user_login_invalid(client: AsyncClient) -> None:
    response = await client.post(
        "/api/access/login", data={"username": "superuser@example1.com", "password": "Test_Password1!"}
    )
    assert response.status_code == 403
