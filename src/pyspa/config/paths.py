from typing import Final

from opdba import utils

BASE_DIR: Final = utils.import_tools.module_to_os_path("opdba")


class ApiPaths:
    OPENAPI_SCHEMA = "/schema"
    API_BASE = "/api"
    HEALTH = "/health"
    # Auth
    ACCESS_TOKEN = "/access/login"  # nosec
    REFRESH_TOKEN = "/access/refresh"  # nosec
    SIGNUP = "/access/signup"
    #


urls = ApiPaths()
