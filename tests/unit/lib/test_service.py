from typing import Any

from app.lib.service.generic import Service


async def test_to_model() -> None:
    class MockService(Service):
        async def to_model(self, data: dict[str, Any], operation: str | None = None) -> dict[str, Any]:
            data["parsed"] = True
            return data

    service = MockService()
    data = {"name": "John", "age": 30}
    expected_data = {"name": "John", "age": 30, "parsed": True}

    parsed_data = await service.to_model(data)

    assert parsed_data == expected_data, f"Expected {expected_data}, but got {parsed_data}"


async def test_new_context_manager() -> None:
    class MockService(Service):
        pass

    async with MockService.new() as service:
        assert isinstance(service, MockService)
