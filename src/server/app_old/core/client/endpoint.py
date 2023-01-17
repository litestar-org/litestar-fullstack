# https://github.com/MikeWooster/api-client/blob/master/apiclient/decorates.py
import inspect
from typing import Any


def endpoint(cls_: Any = None, base_url: Any = None) -> Any:
    """Decorator for automatically constructing urls from a base_url and
    defined resources.

        >>> @endpoint(base_url="https://anywhere.com")
        ... class AnywhereEndpoint:
        ...    all_things = "all-things"
        ...    a_thing = "all-things/{id}"
        ...
        >>> AnywhereEndpoint.all_things
        'https://anywhere.com/all-things'
        >>> AnywhereEndpoint.a_thing.format(id=13)
        'https://anywhere.com/all-things/13'
    """

    def wrap(cls: Any) -> Any:
        return _process_class(cls, base_url)

    if cls_ is None:
        # Decorator is called as @endpoint with parens.
        return wrap
    # Decorator is called as @endpoint without parens.
    return wrap(cls_)


def _process_class(cls: Any, base_url: Any) -> Any:
    if base_url is None:
        raise RuntimeError("A decorated endpoint must define a base_url as @endpoint(base_url='https://foo.com').")
    base_url = base_url.rstrip("/")

    for name, value in inspect.getmembers(cls):
        if name.startswith("_") or inspect.ismethod(value) or inspect.isfunction(value):
            # Ignore any private or class attributes.
            continue
        new_value = str(value).lstrip("/")
        resource = f"{base_url}/{new_value}"
        setattr(cls, name, resource)
    return cls
