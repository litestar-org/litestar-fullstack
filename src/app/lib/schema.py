import msgspec


class Message(msgspec.Struct):
    message: str
