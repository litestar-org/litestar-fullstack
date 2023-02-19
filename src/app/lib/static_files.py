from starlite.config import StaticFilesConfig

from . import settings

config = [
    StaticFilesConfig(
        directories=[settings.app.STATIC_DIR],
        path=settings.app.STATIC_URL,
        name="web",
        html_mode=True,
        opt={"exclude_from_auth": True},
    ),
]
