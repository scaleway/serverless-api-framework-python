from typing import NamedTuple

import click

DEBUG = 0
DEFAULT = 10
INFO = 20
SUCCESS = 30
WARNING = 40
ERROR = 50
CRITICAL = 60

_LOGGER_SINGLETON = None


def get_logger() -> "Logger":
    """Gets the global logger instance."""
    # pylint: disable=global-statement # Known issue FIXME
    global _LOGGER_SINGLETON  # noqa
    # This is the first time we call get_logger, init the singleton
    if not _LOGGER_SINGLETON:
        _LOGGER_SINGLETON = Logger()
    return _LOGGER_SINGLETON


_LogRecord = NamedTuple("LogRecord", [("level", int), ("message", str)])


class Logger:
    """A logger built on top of click.echo."""

    def __init__(self):
        self.level = DEFAULT

    def set_level(self, level: int) -> None:
        """Sets the log level."""
        self.level = level

    def critical(self, message: str) -> None:
        """Logs a critical message."""
        self.log(CRITICAL, message)

    def error(self, message: str) -> None:
        """Logs an error message."""
        self.log(ERROR, message)

    def warning(self, message: str) -> None:
        """Logs a warning message."""
        self.log(WARNING, message)

    def success(self, message: str) -> None:
        """Logs a success message."""
        self.log(SUCCESS, message)

    def info(self, message: str) -> None:
        """Logs an info message."""
        self.log(INFO, message)

    def default(self, message: str) -> None:
        """Logs a message."""
        self.log(DEFAULT, message)

    def debug(self, message: str) -> None:
        """Logs a debug message."""
        self.log(DEBUG, message)

    def log(self, level: int, message: str) -> None:
        """Logs a message with a specific level."""
        self._emit(_LogRecord(message=message, level=level))

    def _emit(self, record: _LogRecord):
        if record.level < self.level:
            return

        err = False
        color = ""
        if record.level in [ERROR, CRITICAL]:
            err = True
            color = "red"
        elif record.level == WARNING:
            color = "yellow"
        elif record.level == INFO:
            color = "cyan"
        elif record.level == SUCCESS:
            color = "green"

        click.echo(click.style(record.message, fg=color), err=err)
