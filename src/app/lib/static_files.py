from pathlib import Path

from litestar.static_files.config import StaticFilesConfig

from . import settings

STATIC_DIRS = [settings.app.STATIC_DIR]
if settings.app.DEBUG:
    STATIC_DIRS.append(Path(settings.BASE_DIR / "domain" / "web" / "resources"))


config = [
    StaticFilesConfig(
        directories=STATIC_DIRS,  # type: ignore[arg-type]
        path=settings.app.STATIC_URL,
        name="web",
        html_mode=False,
        opt={"exclude_from_auth": True},
    ),
]
