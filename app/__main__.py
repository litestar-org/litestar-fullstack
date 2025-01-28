from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import NoReturn


def setup_environment() -> None:
    """Configure the environment variables and path."""
    current_path = Path(__file__).parent.parent.resolve()
    sys.path.append(str(current_path))
    from app.config import get_settings

    settings = get_settings()
    os.environ.setdefault("LITESTAR_APP", "app.asgi:create_app")
    os.environ.setdefault("LITESTAR_APP_NAME", settings.app.NAME)


def run_cli() -> NoReturn:
    """Application Entrypoint.

    This function sets up the environment and runs the Litestar CLI.
    If there's an error loading the required libraries, it will exit with a status code of 1.

    Returns:
        NoReturn: This function does not return as it either runs the CLI or exits the program.

    Raises:
        SystemExit: If there's an error loading required libraries.
    """
    setup_environment()

    try:
        from litestar.cli.main import litestar_group

        sys.exit(litestar_group())
    except ImportError as exc:
        print(  # noqa: T201
            "Could not load required libraries. ",
            "Please check your installation and make sure you activated any necessary virtual environment",
        )
        print(exc)  # noqa: T201
        sys.exit(1)


if __name__ == "__main__":
    run_cli()
