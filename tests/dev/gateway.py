from scw_serverless.app import Serverless

app = Serverless("integration-tests-gateway", gateway_domains=["example.org"])


@app.get("/world", privacy="public", min_scale=1)
def hello_world(_event: dict, _context: dict):
    return "Hello World from gateway!"


@app.get("/mars", privacy="public", min_scale=1)
def hello_mars(_event: dict, _context: dict):
    return "Hello Mars from gateway!"
