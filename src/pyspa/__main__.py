import sys
from pathlib import Path


def main() -> None:
    current_path = Path(__file__).parent.resolve()
    sys.path.append(str(current_path))
    try:
        from pyspa.cli import cli
        from pyspa.config import log_config

        log_config.configure()
    except ImportError:
        print(  # noqa: T201
            "💣 Could not load required libraries.  ",
            "Please check your installation and make sure you activated any necessary virtual environment",
        )
        sys.exit(1)
    cli()
