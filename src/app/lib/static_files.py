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
    """Hosting a custom SAQ UI

    I'd like to serve the static assets as they are from SAQ, but i've not been able to do that.

    I've tried to do something like this:
        STATIC_DIRS.append(Path(utils.module_to_os_path("saq") / "static"))

    This correctly finds and serves the files.  However, the some of the assets are already gzipped.  These are corrupted and unreadable by the browser.
    todo: investigate why Litestar doesn't serve those files correctly.
    # STATIC_DIRS.append(Path(settings.BASE_DIR / "lib" / "worker" / "static"))
    """
    STATIC_DIRS.append(Path(settings.BASE_DIR / "lib" / "worker" / "static"))

config = [
    StaticFilesConfig(
        directories=STATIC_DIRS,  # type: ignore[arg-type]
        path=settings.app.STATIC_URL,
        name="web",
        html_mode=False,
        opt={"exclude_from_auth": True},
    ),
]
