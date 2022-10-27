from scw_serverless.app import Serverless

app = Serverless("integration-tests-gateway", gateway_domains=["example.org"])


@app.get("/", privacy="public")
def hello_world(_event: dict, _context: dict):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """

    return "Hello World from gateway!"
