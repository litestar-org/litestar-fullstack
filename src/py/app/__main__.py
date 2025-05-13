from __future__ import annotations

import os
import sys
from pathlib import Path


def setup_environment() -> None:
    """Configure the environment variables and path."""
    current_path = Path(__file__).parent.parent.resolve()
    sys.path.append(str(current_path))
    from app import config
    from app.lib.settings import get_settings

    _ = config.log.structlog_logging_config.configure()()
    settings = get_settings()
    os.environ.setdefault("LITESTAR_APP", "app.server.asgi:create_app")
    os.environ.setdefault("LITESTAR_APP_NAME", settings.app.NAME)
    os.environ.setdefault("LITESTAR_GRANIAN_IN_SUBPROCESS", "false")
    os.environ.setdefault("LITESTAR_GRANIAN_USE_LITESTAR_LOGGER", "true")


def run_cli() -> None:
    """Application Entrypoint.

    This function sets up the environment and runs the Litestar CLI.
    If there's an error loading the required libraries, it will exit with a status code of 1.
    """
    setup_environment()

    try:
        from litestar.cli.main import litestar_group

        litestar_group()
    except ImportError as exc:
        print(  # noqa: T201
            "Could not load required libraries. ",
            "Please check your installation and make sure you activated any necessary virtual environment",
        )
        print(exc)  # noqa: T201
        sys.exit(1)


if __name__ == "__main__":
    run_cli()
