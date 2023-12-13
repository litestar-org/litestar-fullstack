from __future__ import annotations

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import nodeenv  # type: ignore  # noqa: F401

    NODEENV_INSTALLED = True
except ImportError:
    NODEENV_INSTALLED = False

logger = logging.getLogger()

PROJECT_ROOT = Path(__file__).parent.parent
NODEENV = "nodeenv"
DEFAULT_VENV_PATH = Path(PROJECT_ROOT / ".venv")


def build_npm_assets(setup_kwargs: Any) -> Any:
    # look for this in the environment and skip this function if it exists, sometimes building here is not needed, eg. when using nixpacks
    no_nodeenv = os.environ.get("LITESTAR_SKIP_NODEENV_INSTALL") is not None or NODEENV_INSTALLED is False
    kwargs: dict[str, Any] = {}
    if no_nodeenv:
        logger.info("skipping nodeenv configuration")
    else:
        found_in_local_venv = Path(DEFAULT_VENV_PATH / "bin" / NODEENV).exists()
        nodeenv_command = f"{DEFAULT_VENV_PATH}/bin/{NODEENV}" if found_in_local_venv else NODEENV
        install_dir = DEFAULT_VENV_PATH if found_in_local_venv else os.environ.get("VIRTUAL_ENV", sys.prefix)
        logger.info("Installing Node environment to %s:", install_dir)
        subprocess.run([nodeenv_command, install_dir, "--force", "--quiet"], **kwargs)  # noqa: PLW1510

    if platform.system() == "Windows":
        kwargs["shell"] = True
    logger.info("Installing NPM packages.")
    subprocess.run(["npm", "install"], **kwargs)  # noqa: S607, PLW1510
    logger.info("Building NPM assets.")
    subprocess.run(["npm", "run", "build"], **kwargs)  # noqa: S607, PLW1510
    return setup_kwargs


if __name__ == "__main__":
    build_npm_assets({})
