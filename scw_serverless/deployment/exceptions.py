import logging

from scaleway import ScalewayException


def log_scaleway_exception(exception: ScalewayException) -> None:
    """Log a Scaleway Exception, displaying the error message if present."""
    to_display: str = exception.response.text
    body_json = exception.response.json()
    if "message" in body_json:
        to_display = body_json["message"]
    logging.critical("Could not deploy the application: %s", to_display)
