from pathlib import Path
from typing import Final

from pyspa import utils

BASE_DIR: Final = utils.module_loading.module_to_os_path("pyspa")

PUBLIC_DIR = Path(BASE_DIR, "web/public")
ASSETS_DIR = Path(BASE_DIR, "web/assets")


class ApiPaths:
    OPENAPI_SCHEMA = "/schema"
    HEALTH = "/api/health"
    # Auth
    ACCESS_TOKEN = "/api/access/login"  # nosec
    REFRESH_TOKEN = "/api/access/refresh"  # nosec
    SIGNUP = "/api/access/signup"
    #
    STATIC = "/public"


urls = ApiPaths()
