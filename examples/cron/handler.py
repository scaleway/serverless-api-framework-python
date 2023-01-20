import json
import logging
from typing import Any

from scw_serverless import Serverless

app = Serverless("cron")
logger = logging.getLogger(app.service_name)
logger.setLevel(logging.INFO)


@app.schedule(
    schedule="*/1 * * * 1-5",
    inputs={"myname": "Georges"},
    privacy="public",
)
def hello_cron(event: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    """A simple cron that regularly greets you during business days."""
    body = json.loads(event["body"])
    my_name = body["myname"]
    # Using fstrings in logger is discouraged by pylint
    logger.info("Greetings %s!", my_name)
    return {"statusCode": 200}
