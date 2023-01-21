"""Application."""
from rich import get_console
from rich.traceback import install as rich_tracebacks

from app import domain, lib

__all__ = ["lib", "domain"]

rich_tracebacks(
    console=get_console(),
    suppress=(
        "sqlalchemy",
        "starlite_saqlalchemy",
        "click",
        "rich",
        "saq",
        "starlite",
        "rich_click",
    ),
    show_locals=False,
)
"""Pre-configured traceback handler.  Suppresses some of the frames by default to reduce the amount printed to the screen."""
