from typing import Any

from scw_serverless.app import Serverless

NAMESPACE_NAME = "integration-tests-gateway"

app = Serverless(NAMESPACE_NAME)


@app.get(url="/health")
def health(_event: dict[str, Any], _context: dict[str, Any]):
    return "I'm fine!"


@app.get(url="/messages")
def get_messages(_event: dict[str, Any], _context: dict[str, Any]):
    return "Could not find any message"


@app.post(url="/messages/new")
def post_message(event: dict[str, Any], _context: dict[str, Any]):
    return {"statusCode": 200, "body": f'Message {event["body"]} successfully created!'}


@app.put(url="/messages/")
def put_message(event: dict[str, Any], _context: dict[str, Any]):
    path: str = event["path"]
    message = path.removeprefix("/messages/")
    return {"statusCode": 200, "body": f"Message {message} successfully created!"}
