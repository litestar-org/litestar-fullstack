import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    "username,password,expected_status_code",
    (
        ("superuser@example1.com", "Test_Password1!", 403),
        ("superuser@example.com", "Test_Password1!", 201),
        ("user@example.com", "Test_Password1!", 403),
        ("user@example.com", "Test_Password2!", 201),
        ("inactive@example.com", "Old_Password2!", 403),
        ("inactive@example.com", "Old_Password3!", 403),
    ),
)
async def test_user_login(client: AsyncClient, username: str, password: str, expected_status_code: int) -> None:
    response = await client.post("/api/access/login", data={"username": username, "password": password})
    assert response.status_code == expected_status_code
