import pytest

from app.lib.settings import get_settings

pytestmark = pytest.mark.anyio


def test_app_slug() -> None:
    """Test app name conversion to slug."""
    settings = get_settings()
    settings.app.NAME = "My Application!"
    assert settings.app.slug == "my-application"
