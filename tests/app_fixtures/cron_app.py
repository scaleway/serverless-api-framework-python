from scw_serverless.app import Serverless
from scw_serverless.config.triggers import CronTrigger

app = Serverless("helloworld")


@app.schedule(
    schedule=CronTrigger(name="monday", schedule="0 0 * * MON"),
    inputs={"my_name": "Georges"},
    description="This is a description",
    privacy="public",
    env={"key": "value", "PYTHONUNBUFFERED": "true"},
)
def hello_world_cron(event: dict, _context: dict):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """
    print(f'Hello {event["my_name"]}!')
    return {"statusCode": 200}
