# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

import sys
from pathlib import Path

__all__ = ["run_cli"]


def run_cli() -> None:
    """Application Entrypoint."""
    current_path = Path(__file__).parent.resolve()
    sys.path.append(str(current_path))
    try:
        from app import cli

    except ImportError:
        print(  # noqa: T201
            "💣 Could not load required libraries.  ",
            "Please check your installation and make sure you activated any necessary virtual environment",
        )
        sys.exit(1)
    cli.app()


if __name__ == "__main__":
    run_cli()
