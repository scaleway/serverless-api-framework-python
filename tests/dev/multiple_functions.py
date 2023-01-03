from typing import Any

from scw_serverless.app import Serverless

app = Serverless("integration-tests")


@app.func(memory_limit=256)
def hello_world(_event: dict[str, Any], _context: dict[str, Any]):
    return "Hello World!"


@app.func(memory_limit=256)
def cloud_of_choice(_event: dict[str, Any], _context: dict[str, Any]):
    return "The cloud of choice"


@app.func(memory_limit=256)
def scaleway(_event: dict[str, Any], _context: dict[str, Any]):
    return "Scaleway"
