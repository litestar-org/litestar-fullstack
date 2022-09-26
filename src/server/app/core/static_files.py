from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlite import HTTPException, StaticFilesConfig

from app.config import paths

config = [StaticFilesConfig(directories=[paths.PUBLIC_DIR], path=paths.urls.STATIC)]
"""Static files config"""


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> "Response":
        try:
            return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == 404:
                return await super().get_response(f"{paths.PUBLIC_DIR}/index.html", scope)
            raise ex
