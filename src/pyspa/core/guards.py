from typing import TYPE_CHECKING, Any, Optional

from starlite import BaseRouteHandler, NotAuthorizedException, Request

if TYPE_CHECKING:
    from collections.abc import Callable


class CheckPayloadMismatch:
    """Creates a callable class instance that can be used as a Guard function
    to check that path variables are equal to payload counterparts.

    Default behaviour is for the path variables to be coerced to a `str` before the
    comparison. This supports the common case of comparing a `str` identity from
    the payload to a UUID path parameter that has already been parsed into a UUID
    object.

    Parameters
    ----------
    payload_key : str
        Used to extract the value from the payload. If the key does not exist in
        the payload the value of the path parameter will be compared against `None`.
    path_key : str
        Name of the path parameter. This must be the name of a path parameter on
        the route to which the guard is applied, otherwise will raise `KeyError` at runtime.
    compare_fn : Callable[[Any, Any], bool] | None
        For custom comparison logic, pass a two parameter callable here that returns
        a `bool`.
    """

    def __init__(
        self,
        payload_key: str,
        path_key: str,
        compare_fn: Optional["Callable[[Any, Any], bool]"] = None,
    ) -> None:
        self.payload_key = payload_key
        self.path_key = path_key
        if compare_fn is not None:
            self.compare_fn = staticmethod(compare_fn)
        else:
            self.compare_fn = self._compare

    @staticmethod
    def _compare(payload_value: Any, path_value: Any) -> bool:
        return payload_value == str(path_value)  # type:ignore[no-any-return]

    async def __call__(self, request: Request, _: BaseRouteHandler) -> None:
        """Ensure value of `self.payload_key` key in request payload matches
        the value of `self.path_key` in `Request.path_params`.

        By default, calls `str` on both values before comparing. For custom comparison
        provide a callable to `compare_fn` on instantiation.

        Parameters
        ----------
        request : Request
        _ : BaseRouteHandler

        Raises
        ------
        NotAuthorizedException
            If the value retrieved from the path does not test equal to the value
            retrieved from the request payload.
        """
        payload = await request.json() or {}
        payload_value = payload.get(self.payload_key)
        path_value = str(request.path_params[self.path_key])
        if not self.compare_fn(payload_value, path_value):
            raise NotAuthorizedException
