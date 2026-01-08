from __future__ import annotations

import argparse
import logging
import platform
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger("manage_assets")

PROJECT_ROOT = Path(__file__).parent.parent


def manage_resources(setup_kwargs: Any) -> Any:
    """Manage frontend assets using bun.

    Args:
        setup_kwargs: Setup configuration with optional build_assets and install_packages flags.

    Returns:
        The setup_kwargs with processed flags removed.
    """
    build_assets = setup_kwargs.pop("build_assets", None)
    install_packages = setup_kwargs.pop("install_packages", None)
    kwargs: dict[str, Any] = {}

    if platform.system() == "Windows":
        kwargs["shell"] = True

    web_dir = PROJECT_ROOT / "src/js/web"

    if install_packages is not None:
        logger.info("Installing packages with bun.")
        subprocess.run(["bun", "install"], **kwargs, cwd=web_dir)  # noqa: S607, PLW1510

    if build_assets is not None:
        logger.info("Building frontend assets with bun.")
        subprocess.run(["bun", "run", "build"], **kwargs, cwd=web_dir)  # noqa: S607, PLW1510

    return setup_kwargs


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Manage Resources")
    parser.add_argument("--build-assets", action="store_true", help="Build assets for static hosting.", default=None)
    parser.add_argument("--install-packages", action="store_true", help="Install packages with bun.", default=None)
    args = parser.parse_args()
    setup_kwargs = {"build_assets": args.build_assets, "install_packages": args.install_packages}
    manage_resources(setup_kwargs)
