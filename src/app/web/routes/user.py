import logging

from sqlalchemy.ext.asyncio import AsyncSession
from starlite import Body, MediaType, Request, RequestEncodingType, post

from app import schemas, services
from app.config.paths import urls

logger = logging.getLogger(__name__)


# Given an instance of 'JWTAuth' we can create a login handler function:
@post(path=urls.ACCESS_TOKEN, media_type=MediaType.JSON, cache=False, tags=["Access"])
async def login(
    db: AsyncSession, request: Request, data: schemas.UserLogin = Body(media_type=RequestEncodingType.URL_ENCODED)
) -> schemas.User:
    # we have a user instance - probably by retrieving it from persistence using another lib.
    # what's important for our purposes is to have an identifier:
    user = await services.user.authenticate(db, data.username, data.password)
    request.set_session({"user_id": user.id})
    logger.info(f"authenticated user: {user.email}")
    return schemas.User.from_orm(user)


@post(path=urls.SIGNUP, tags=["Access"])
async def signup(db: AsyncSession, request: Request, data: schemas.UserSignup) -> schemas.User:
    user = await services.user.create(db, data)
    request.set_session({"user_id": user.id})
    return schemas.User.from_orm(user)
