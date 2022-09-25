import logging

from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from starlite import Body, Parameter, RequestEncodingType, UploadFile, post
from starlite.controller import Controller

from app.core import guards
from app.schemas import CamelizedBaseSchema

logger = logging.getLogger(__name__)


class FormData(CamelizedBaseSchema):
    collection: UploadFile
    variable_t: int

    class Config:
        arbitrary_types_allowed = True


class CollectionController(Controller):
    path = "/team/{team_id:uuid}"
    guards = [guards.requires_team_membership, guards.requires_active_user]

    @post(path="/upload")
    async def upload_file(
        self,
        db: AsyncSession,
        team_id: UUID4 = Parameter(
            title="Team ID",
            description="The identifier for the uploaded file's team",
        ),
        data: FormData = Body(media_type=RequestEncodingType.MULTI_PART),
    ) -> dict[str, str]:
        """Upload a file"""

        logger.info("Processing Uploaded File")
        return {
            "status": "file uploaded",
        }
