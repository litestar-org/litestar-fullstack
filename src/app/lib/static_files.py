from pathlib import Path

from litestar.static_files.config import StaticFilesConfig

from . import settings

STATIC_DIRS = [settings.app.BUNDLE_DIR]
if settings.app.DEV_MODE and settings.app.HOT_RELOAD:
    STATIC_DIRS.append(Path(settings.RESOURCE_DIR))


config = [
    StaticFilesConfig(
        directories=STATIC_DIRS,  # type: ignore[arg-type]
        path=settings.app.STATIC_URL,
        name="web",
        html_mode=False,
        opt={"exclude_from_auth": True},
    ),
]
"""Static file configuration."""
