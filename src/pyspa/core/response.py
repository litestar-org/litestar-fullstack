from typing import Any

from asyncpg.pgproto import pgproto
from starlite import Response as _Response


class Response(_Response):
    @staticmethod
    def serializer(value: Any) -> Any:
        """
        Custom serializer method that handles the `asyncpg.pgproto.UUID` implementation.

        Parameters
        ----------
        value : Any

        Returns
        -------
        Any
        """
        if isinstance(value, pgproto.UUID):
            return str(value)
        return _Response.serializer(value)
