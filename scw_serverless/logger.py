import click

DEBUG = 0
DEFAULT = 10
INFO = 20
SUCCESS = 30
WARNING = 40
ERROR = 50
CRITICAL = 60


def get_logger():
    return Logger()


class _LogRecord:
    def __init__(self, message: str = None, level: int = 0):
        self.message = message
        self.level = level


class Logger:
    def __init__(self):
        self.level = DEFAULT

    def set_level(self, level: int):
        self.level = level

    def critical(self, message: str):
        self.log(CRITICAL, message)

    def error(self, message: str):
        self.log(ERROR, message)

    def warning(self, message: str):
        self.log(WARNING, message)

    def success(self, message: str):
        self.log(SUCCESS, message)

    def info(self, message: str):
        self.log(INFO, message)

    def default(self, message: str):
        self.log(DEFAULT, message)

    def debug(self, message: str):
        self.log(DEBUG, message)

    def log(self, level: int, message: str):
        self.emit(_LogRecord(message=message, level=level))

    def emit(self, record: _LogRecord):
        if record.level < self.level:
            return

        err = False
        fg = ""
        if record.level == ERROR or record.level == CRITICAL:
            err = True
            fg = "red"
        elif record.level == WARNING:
            fg = "yellow"
        elif record.level == INFO:
            fg = "cyan"
        elif record.level == SUCCESS:
            fg = "green"

        click.echo(click.style(record.message, fg=fg), err=err)
