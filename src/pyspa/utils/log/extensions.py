import logging
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Iterable, List, Optional, Type, Union

import picologging
from rich import get_console
from rich._log_render import FormatTimeCallable, LogRender
from rich.highlighter import Highlighter, ReprHighlighter
from rich.text import Text
from rich.traceback import Traceback
from starlette.status import HTTP_200_OK

if TYPE_CHECKING:
    from types import ModuleType

    from rich.console import Console, ConsoleRenderable


class RichPicologgingHandler(picologging.Handler):  # type: ignore
    """A logging handler that renders output with Rich. The time / level / message and file are displayed in columns.
    The level is color coded, and the message is syntax highlighted.

    Note:
        Be careful when enabling console markup in log messages
         if you have configured logging for libraries not
        under your control. If a dependency writes messages containing square brackets,
         it may not produce the intended output.

    Args:
        level (Union[int, str], optional): Log level. Defaults to logging.NOTSET.
        console (:class:`~rich.console.Console`, optional): Optional console instance to write logs.
            Default will use a global console instance writing to stdout.
        show_time (bool, optional): Show a column for the time. Defaults to True.
        omit_repeated_times (bool, optional): Omit repetition of the same time. Defaults to True.
        show_level (bool, optional): Show a column for the level. Defaults to True.
        show_path (bool, optional): Show the path to the original log call. Defaults to True.
        enable_link_path (bool, optional): Enable terminal link of path column to file. Defaults to True.
        highlighter (Highlighter, optional): Highlighter to style log messages,
         or None to use ReprHighlighter. Defaults to None.
        markup (bool, optional): Enable console markup in log messages. Defaults to False.
        rich_tracebacks (bool, optional): Enable rich tracebacks with syntax
         highlighting and formatting. Defaults to False.
        tracebacks_width (Optional[int], optional): Number of characters used to render
         tracebacks, or None for full width. Defaults to None.
        tracebacks_extra_lines (int, optional): Additional lines of code to render tracebacks,
         or None for full width. Defaults to None.
        tracebacks_theme (str, optional): Override pygments theme used in traceback.
        tracebacks_word_wrap (bool, optional): Enable word wrapping of long tracebacks lines. Defaults to True.
        tracebacks_show_locals (bool, optional): Enable display of locals in tracebacks. Defaults to False.
        tracebacks_suppress (Sequence[Union[str, ModuleType]]): Optional sequence of modules or paths
         to exclude from traceback.
        locals_max_length (int, optional): Maximum length of containers before abbreviating,
         or None for no abbreviation.  Defaults to 10.
        locals_max_string (int, optional): Maximum length of string before truncating,
         or None to disable. Defaults to 80.
        log_time_format (Union[str, TimeFormatterCallable], optional): If ``log_time``
         is enabled, either string for strftime or callable that formats the time. Defaults to "[%x %X] ".
        keywords (List[str], optional): List of words to highlight instead of ``RichHandler.KEYWORDS``.
    """

    KEYWORDS: ClassVar[Optional[List[str]]] = [
        "GET",
        "POST",
        "HEAD",
        "PUT",
        "DELETE",
        "OPTIONS",
        "TRACE",
        "PATCH",
    ]
    HIGHLIGHTER_CLASS: ClassVar[Type[Highlighter]] = ReprHighlighter

    def __init__(
        self,
        level: "Union[int, str]" = picologging.NOTSET,
        console: "Optional[Console]" = None,
        *,
        show_time: bool = True,
        omit_repeated_times: bool = True,
        show_level: bool = True,
        show_path: bool = True,
        enable_link_path: bool = True,
        highlighter: "Optional[Highlighter]" = None,
        markup: bool = False,
        rich_tracebacks: bool = False,
        tracebacks_width: Optional[int] = None,
        tracebacks_extra_lines: int = 3,
        tracebacks_theme: Optional[str] = None,
        tracebacks_word_wrap: bool = True,
        tracebacks_show_locals: bool = False,
        tracebacks_suppress: "Iterable[Union[str, ModuleType]]" = (),
        locals_max_length: int = 10,
        locals_max_string: int = 80,
        log_time_format: "Union[str, FormatTimeCallable]" = "[%x %X]",
        keywords: "Optional[List[str]]" = None,
    ) -> None:
        super().__init__(level=level)
        self.console = console or get_console()
        self.highlighter = highlighter or self.HIGHLIGHTER_CLASS()
        self._log_render = LogRender(
            show_time=show_time,
            show_level=show_level,
            show_path=show_path,
            time_format=log_time_format,
            omit_repeated_times=omit_repeated_times,
            level_width=None,
        )
        self.enable_link_path = enable_link_path
        self.markup = markup
        self.rich_tracebacks = rich_tracebacks
        self.tracebacks_width = tracebacks_width
        self.tracebacks_extra_lines = tracebacks_extra_lines
        self.tracebacks_theme = tracebacks_theme
        self.tracebacks_word_wrap = tracebacks_word_wrap
        self.tracebacks_show_locals = tracebacks_show_locals
        self.tracebacks_suppress = tracebacks_suppress
        self.locals_max_length = locals_max_length
        self.locals_max_string = locals_max_string
        self.keywords = keywords

    def get_level_text(self, record: picologging.LogRecord) -> "Text":
        """Get the level name from the record.

        Args:
            record (LogRecord): LogRecord instance.

        Returns:
            Text: A tuple of the style and level name.
        """
        level_name = record.levelname
        level_text = Text.styled(level_name.ljust(8), f"picologging.level.{level_name.lower()}")
        return level_text

    def emit(self, record: picologging.LogRecord) -> None:
        """Invoked by logging."""
        message = self.format(record)
        traceback = None
        if self.rich_tracebacks and record.exc_info and record.exc_info != (None, None, None):
            exc_type, exc_value, exc_traceback = record.exc_info
            traceback = Traceback.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                width=self.tracebacks_width,
                extra_lines=self.tracebacks_extra_lines,
                theme=self.tracebacks_theme,
                word_wrap=self.tracebacks_word_wrap,
                show_locals=self.tracebacks_show_locals,
                locals_max_length=self.locals_max_length,
                locals_max_string=self.locals_max_string,
                suppress=self.tracebacks_suppress,
            )
            message = record.getMessage()
            if self.formatter:
                record.message = record.getMessage()
                formatter = self.formatter
                if hasattr(formatter, "usesTime") and formatter.usesTime():
                    record.asctime = formatter.formatTime(record, formatter.datefmt)
                message = formatter.formatMessage(record)

        message_renderable = self.render_message(record, message)
        log_renderable = self.render(record=record, traceback=traceback, message_renderable=message_renderable)
        try:
            self.console.print(log_renderable)
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)

    def render_message(self, record: picologging.LogRecord, message: str) -> "ConsoleRenderable":
        """Render message text in to Text.

        record (LogRecord): logging Record.
        message (str): String containing log message.

        Returns:
            ConsoleRenderable: Renderable to display log message.
        """
        use_markup = getattr(record, "markup", self.markup)
        message_text = Text.from_markup(message) if use_markup else Text(message)

        highlighter = getattr(record, "highlighter", self.highlighter)
        if highlighter:
            message_text = highlighter(message_text)

        if self.keywords is None:
            self.keywords = self.KEYWORDS

        if self.keywords:
            message_text.highlight_words(self.keywords, "logging.keyword")

        return message_text

    def render(
        self,
        *,
        record: picologging.LogRecord,
        traceback: "Optional[Traceback]",
        message_renderable: "ConsoleRenderable",
    ) -> "ConsoleRenderable":
        """Render log for display.

        Args:
            record (LogRecord): logging Record.
            traceback (Optional[Traceback]): Traceback instance or None for no Traceback.
            message_renderable (ConsoleRenderable): Renderable (typically Text) containing log message contents.

        Returns:
            ConsoleRenderable: Renderable to display log.
        """
        path = Path(record.pathname).name
        level = self.get_level_text(record)
        time_format = None if self.formatter is None else self.formatter.datefmt
        log_time = datetime.fromtimestamp(record.created)

        log_renderable = self._log_render(
            self.console,
            [message_renderable] if not traceback else [message_renderable, traceback],
            log_time=log_time,
            time_format=time_format,
            level=level,
            path=path,
            line_no=record.lineno,
            link_path=record.pathname if self.enable_link_path else None,
        )
        return log_renderable


class AccessLogFilter(logging.Filter):
    """
    Filter for omitting log records from uvicorn access logs based on request path.

    Parameters
    ----------
    *args : Any
        Unpacked into [`logging.Filter.__init__()`][logging.Filter].
    path_re : str
        Regex, paths matched are filtered.
    **kwargs : Any
        Unpacked into [`logging.Filter.__init__()`][logging.Filter].
    """

    def __init__(self, *args: Any, path_re: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.path_filter = re.compile(path_re)

    def filter(self, record: picologging.LogRecord) -> bool:
        *_, req_path, _, status_code = record.args
        if self.path_filter.match(req_path) and status_code == HTTP_200_OK:
            return False
        return True


class PicologgingAccessLogFilter(picologging.Filter):  # type: ignore
    """
    Filter for omitting log records from uvicorn access logs based on request path.

    Parameters
    ----------
    *args : Any
        Unpacked into [`logging.Filter.__init__()`][logging.Filter].
    path_re : str
        Regex, paths matched are filtered.
    **kwargs : Any
        Unpacked into [`logging.Filter.__init__()`][logging.Filter].
    """

    def __init__(self, *args: Any, path_re: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.path_filter = re.compile(path_re)

    def filter(self, record: picologging.LogRecord) -> bool:
        *_, req_path, _, status_code = record.args
        if self.path_filter.match(req_path) and status_code == HTTP_200_OK:
            return False
        return True
