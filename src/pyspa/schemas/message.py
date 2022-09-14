from pyspa.schemas.base import CamelizedBaseSchema


class Message(CamelizedBaseSchema):
    message: str
