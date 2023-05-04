import logging


def configure_logger(verbose: bool = False, log_level: int = logging.INFO) -> None:
    """Configure the root logger based on log_level and verbosity."""
    if verbose:
        logging.basicConfig(
            format=" %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
            level=logging.DEBUG,
        )
    else:
        logging.basicConfig(format="%(levelname)-8s: %(message)s", level=log_level)
