import importlib.util
from pathlib import Path

from litestar.static_files.config import StaticFilesConfig

from app import utils

from . import settings

SAQ_INSTALLED = False
if importlib.util.find_spec("saq") is not None:
    SAQ_INSTALLED = True

STATIC_DIRS = [settings.app.STATIC_DIR]
if settings.app.DEBUG:
    STATIC_DIRS.append(Path(settings.BASE_DIR / "domain" / "web" / "resources"))

if SAQ_INSTALLED and settings.worker.WEB_ENABLED:
    STATIC_DIRS.append(Path(utils.module_to_os_path("saq") / "static"))


config = [
    StaticFilesConfig(
        directories=STATIC_DIRS,  # type: ignore[arg-type]
        path=settings.app.STATIC_URL,
        name="web",
        html_mode=True,
        opt={"exclude_from_auth": True},
    ),
]
