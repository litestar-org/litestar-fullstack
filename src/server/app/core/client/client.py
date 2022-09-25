from typing import Any

import httpx
from starlite.exceptions import ServiceUnavailableException


class ClientException(ServiceUnavailableException):
    """Exception for wrapping `httpx` exceptions which will return a `503
    SERVICE UNAVAILABLE` to the api client."""


class HttpClient:
    """Base class for HTTP clients.

    client = HttpClient()
    response = client.request("GET", "/some/resource")
    assert response.status_code == 200
    """

    _client = httpx.AsyncClient()

    async def request(self, *args: Any, **kwargs: Any) -> httpx.Response:
        """Passes `*args`, `**kwargs` straight through to
        `httpx.AsyncClient.request`. Calls `raise_for_status()` on the
        response, handles any HTTPX error by returning a 503 response to
        client.

        Parameters
        ----------
        args : Any
        kwargs : Any
            `args` and `kwargs` passed straight through to `httpx.AsyncClient.request`.

        Returns
        -------
        httpx.Response
        """
        try:
            r = await self._client.request(*args, **kwargs)
            r.raise_for_status()
        except httpx.HTTPError as e:
            url = e.request.url
            raise ClientException(f"Client Error for '{url}'") from e
        return r

    def json(self, response: httpx.Response) -> Any:
        """
        Abstracts deserializing to allow for optional unwrapping of server response, e.g.,
        `{"data": []}`.

        Parameters
        ----------
        response : httpx.Response

        Returns
        -------
        Any
            The result of `httpx.Response.json()` after passing through `self.unwrap_json()`.
        """
        return self.unwrap_json(response.json())

    @staticmethod
    def unwrap_json(data: Any) -> Any:
        """Callback for extracting nested data from the server response.

        Parameters
        ----------
        data : Any
            The JSON response from the server.

        Returns
        -------
        Any
        """
        return data

    @classmethod
    async def close(cls) -> None:
        """Close the client connection."""
        await cls._client.aclose()


async def on_shutdown() -> None:
    """Passed to `Starlite.on_shutdown`."""
    await HttpClient.close()
