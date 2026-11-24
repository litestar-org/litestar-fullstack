from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def setup_environment() -> None:
    """Configure environment variables and Litestar CLI help loading."""
    current_path = Path(__file__).parent.parent.resolve()
    sys.path.append(str(current_path))
    from litestar.cli._utils import LitestarExtensionGroup

    from app import config
    from app.lib.settings import get_settings

    _ = config.log.structlog_logging_config.configure()()
    settings = get_settings()
    os.environ.setdefault("LITESTAR_APP", "app.server.asgi:create_app")
    os.environ.setdefault("LITESTAR_APP_NAME", settings.app.NAME)
    original_format_help = LitestarExtensionGroup.format_help

    def fixed_format_help(self: Any, ctx: Any, formatter: Any) -> None:
        """Ensure plugins are loaded before formatting CLI help."""
        self._prepare(ctx)
        return original_format_help(self, ctx, formatter)

    setattr(LitestarExtensionGroup, "format_help", fixed_format_help)


def run_cli() -> None:
    """Application CLI entrypoint."""
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
