from starlite import MediaType, get

from pyspa.config import settings


@get(path="/health", media_type=MediaType.JSON, cache=False, tags=["Misc"])
async def health_check() -> dict[str, str]:
    """Health check handler"""
    return {"app": settings.app.NAME, "build": settings.app.BUILD_NUMBER}
