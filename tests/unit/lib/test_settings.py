from app.lib import settings


def test_app_slug() -> None:
    """Test app name conversion to slug."""
    settings.app.NAME = "My Application!"
    assert settings.app.slug == "my-application"
