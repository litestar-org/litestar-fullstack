import logging

from sqlalchemy.ext.asyncio import AsyncSession
from starlite import Body, MediaType, RequestEncodingType, Response, post

from pyspa import schemas, services
from pyspa.config.paths import urls
from pyspa.core import security

logger = logging.getLogger(__name__)


# Given an instance of 'JWTAuth' we can create a login handler function:
@post(path=urls.ACCESS_TOKEN, media_type=MediaType.JSON, cache=False, tags=["Access"])
async def user_login(
    db: AsyncSession,
    data: schemas.UserLogin = Body(media_type=RequestEncodingType.URL_ENCODED),
) -> Response[schemas.User]:
    # we have a user instance - probably by retrieving it from persistence using another lib.
    # what's important for our purposes is to have an identifier:
    user = await services.user.authenticate(db, data.username, data.password)
    response = security.oauth2_authentication.login(identifier=str(user.id), response_body=user)
    logger.info(response.headers["authorization"])

    # you can do whatever you want to update the response instance here
    # e.g. response.set_cookie(...)

    return response
