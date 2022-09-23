from scw_serverless.events.schedule import CronSchedule
from scw_serverless.app import Serverless

app = Serverless("helloworld", env={"key1": "value1"}, secret={"key2": "value2"})


@app.schedule(
    schedule=CronSchedule("1", "*", "*", "*", "*", "*"),
    inputs={"my_name": "Georges"},
    description="This is a description",
    privacy="public",
    env={"key": "value"},
    custom_domains=["domain.scw.cloud"],
)
def hello_world_cron(event: dict, _context: dict):
    """handle a request to the function
    Args:
        event (dict): request params
        context (dict): function call metadata
    """
    return f'Hello {event["my_name"]}!'