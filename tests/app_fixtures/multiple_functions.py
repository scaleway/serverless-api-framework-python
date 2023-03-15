from typing import Any

from scw_serverless.app import Serverless

MESSAGES = {
    "hello-world": "Hello World!",
    "cloud-of-choice": "The cloud of choice!",
    "scaleway": "Scaleway",
}

app = Serverless("integration-tests")


@app.func(memory_limit=256)
def hello_world(_event: dict[str, Any], _context: dict[str, Any]):
    return MESSAGES["hello-world"]


@app.func(memory_limit=256)
def cloud_of_choice(_event: dict[str, Any], _context: dict[str, Any]):
    return MESSAGES["cloud-of-choice"]


@app.func(memory_limit=256)
def scaleway(_event: dict[str, Any], _context: dict[str, Any]):
    return MESSAGES["scaleway"]
