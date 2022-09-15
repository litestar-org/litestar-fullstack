from pathlib import Path
from typing import Final

from pyspa import utils

BASE_DIR: Final = utils.import_tools.module_to_os_path("pyspa")

PUBLIC_DIR = Path(BASE_DIR, "web/public")
ASSETS_DIR = Path(BASE_DIR, "web/assets")


class ApiPaths:
    OPENAPI_SCHEMA = "/schema"
    API_BASE = "/api"
    HEALTH = "/health"
    # Auth
    ACCESS_TOKEN = "/access/login"  # nosec
    REFRESH_TOKEN = "/access/refresh"  # nosec
    SIGNUP = "/access/signup"
    #
    STATIC = "/public"


urls = ApiPaths()
