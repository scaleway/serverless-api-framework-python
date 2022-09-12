import os.path
import sys

sys.path.insert(0, os.path.abspath("../serverless"))

from app import Serverless # I don't know why but I can't import Serverless otherwise...

app = Serverless("helloworld")


@app.func(url="/")
def hello_world(event: dict, context: dict):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return "Hello World!"
