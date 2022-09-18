from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from pyspa.config import settings

__all__ = ["console"]

console = Console(
    markup=True,
    emoji=True,
    color_system="truecolor",
    stderr=False,
)
TEXT_LOGO = """
[bold yellow]✨ Starlite
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
            custom_header = f"[bold blue]✨ {settings.app.NAME}"
        console.print(Panel(custom_header, height=10, width=console.width), overflow="ellipsis")
        console.print(Rule(title=command_title))
