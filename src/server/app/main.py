# pylint: disable=[invalid-name,import-outside-toplevel]
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from starlite import Starlite


def run_cli() -> None:
    """Application Entrypoint."""
    current_path = Path(__file__).parent.resolve()
    sys.path.append(str(current_path))
    try:
        from app import cli

    except ImportError:
        print(
            "💣 Could not load required libraries.  ",
            "Please check your installation and make sure you activated any necessary virtual environment",
        )
        sys.exit(1)
    cli.app()


def run_app() -> Starlite:
    """Create ASGI application."""
    from starlite import Starlite

    from app import api
    from app.lib import plugins

    return Starlite(route_handlers=[api.urls.example_handler], on_app_init=[plugins.saqlalchemy])


if __name__ == "__main__":
    run_cli()
