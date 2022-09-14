import logging

from starlite import Body, RequestEncodingType, UploadFile, post

from pyspa.schemas import CamelizedBaseSchema

logger = logging.getLogger(__name__)


class FormData(CamelizedBaseSchema):
    collection: UploadFile
    variable_t: int

    class Config:
        arbitrary_types_allowed = True


@post(
    path="/upload",
    cache=False,
    tags=["Collection"],
)
async def handle_collection_upload(
    data: FormData = Body(media_type=RequestEncodingType.MULTI_PART),
) -> dict[str, str]:
    """Upload a file"""
    logger.info("Processing Uploaded File")
    return {
        "status": "file uploaded",
    }
