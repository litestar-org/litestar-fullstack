from __future__ import annotations


def start_app() -> None:
    """Application Management Entrypoint.

    This is here for convenience due to its ubiquitous usage in Django.

    This invokes the same as the `app` command (`python -m app`).
    """
    import sys
    from pathlib import Path

    current_path = Path(__file__).parent.resolve()
    sys.path.append(str(current_path))

    from app.__main__ import run_cli

    run_cli()


if __name__ == "__main__":
    start_app()
