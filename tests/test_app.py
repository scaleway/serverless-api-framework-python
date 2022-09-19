from serverless.app import _Function, _ScheduledFunction
from serverless.events.cron import Cron


def handler(event, context):
    return ""


def test_function_get_config():
    expected = {
        "handler": "test_app.handler",
        "minScale": 0,
        "maxScale": 20,
    }
    fn = _Function(handler, args={"min_scale": 0, "max_scale": 20})
    assert fn.get_config() == expected


def test_scheduled_function_get_config():
    expected = {
        "handler": "test_app.handler",
        "minScale": 0,
        "maxScale": 20,
        "events": [{"schedule": {"rate": "* * * * 7"}}],
    }
    fn = _ScheduledFunction(
        Cron("*", "*", "*", "*", "*", "7"),
        None,
        handler,
        args={"min_scale": 0, "max_scale": 20},
    )
    assert fn.get_config() == expected


def test_scheduled_function_get_config_with_input():
    expected = {
        "handler": "test_app.handler",
        "minScale": 0,
        "maxScale": 20,
        "events": [
            {"schedule": {"rate": "* * * * 7", "input": {"my_name": "Georges"}}}
        ],
    }
    fn = _ScheduledFunction(
        Cron("*", "*", "*", "*", "*", "7"),
        {"my_name": "Georges"},
        handler,
        args={"min_scale": 0, "max_scale": 20},
    )
    assert fn.get_config() == expected
