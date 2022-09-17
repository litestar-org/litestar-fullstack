from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from pyspa.config import settings

__all__ = ["console"]

console = Console(
    markup=True,
    emoji=True,
    color_system="truecolor",
    stderr=False,
)
TEXT_LOGO = """
Starlite
"""


def print_prologue(
    is_interactive: bool,
    custom_header: str = "",
    command_title: str = "Run Logs",
) -> None:
    """Prints the CLI application header
    Args:
        is_interactive (bool): Whether the console is interactive
        base_params (dict): The base params for dynamic header
        custom_header (str, optional): The custom header. Defaults to "".
        command_title (str): The command title
    Returns:
        None
    """
    if is_interactive:
        if not custom_header:
            custom_header = settings.app.NAME
        console.print(
            Columns(
                (
                    Panel(Text.from_ansi(TEXT_LOGO), width=26, height=11),
                    Panel(
                        custom_header,
                        height=11,
                        width=max(35, console.width - 27),
                    ),
                ),
            ),
            overflow="ellipsis",
        )
        console.print(Rule(title=command_title))
