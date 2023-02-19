from starlite.config import StaticFilesConfig

from .settings import PUBLIC_DIR, STATIC_PATH

config = [
    StaticFilesConfig(
        directories=[PUBLIC_DIR],
        path=STATIC_PATH,
        name="web",
        html_mode=True,
        opt={"exclude_from_auth": True},
    ),
]
