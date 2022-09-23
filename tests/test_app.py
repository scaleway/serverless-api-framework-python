from dev.app import app
from scw_serverless.app import Serverless
from scw_serverless.app import _Function, _ScheduledFunction
from scw_serverless.events.schedule import Cron


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


def test_module_to_path():
    serverless = Serverless("unit_test")
    assert serverless.module_to_path("abc.def") == "abc/def"


def test_function_export():
    """
    Test if annotation are correctly exported and stored in the functions list.
    This test use the file dev/app.py
    :return:
    """
    assert len(app.functions) == 1
