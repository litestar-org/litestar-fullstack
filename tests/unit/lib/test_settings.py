import pytest

from app.config import settings

pytestmark = pytest.mark.anyio


def test_app_slug() -> None:
    """Test app name conversion to slug."""
    settings.app.NAME = "My Application!"
    assert settings.app.slug == "my-application"
