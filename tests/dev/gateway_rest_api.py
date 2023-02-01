from scw_serverless.app import Serverless

app = Serverless("integration-tests-gateway", gateway_domains=["example.org"])


@app.get("/messages", privacy="public")
def get_messages(_event: dict, _context: dict):
    return "Hello World from gateway!"


@app.post("/messages", privacy="public")
def post_message(_event: dict, _context: dict):
    return "Hello Mars from gateway!"


@app.put("/messages", privacy="public")
def put_message(_event: dict, _context: dict):
    return "Hello Mars from gateway!"


# Not very rest-like
@app.get("/messages/latest", privacy="public")
def get_latest_messages(_event: dict, _context: dict):
    return "Hello Mars from gateway!"
