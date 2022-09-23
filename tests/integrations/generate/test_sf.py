from tests.integrations.utils import serverless_framework


def test_integration_serverless_framework():
    serverless_framework("tests/dev/app.py")


def test_integration_serverless_framework_multiple_functions():
    serverless_framework("tests/dev/multiple-functions.py")


def test_integration_serverless_framework_existing_function():
    project_id = serverless_framework("tests/dev/app.py", do_cleanup=False)
    serverless_framework("tests/dev/app.py", do_cleanup=True, project_id=project_id)


def test_integration_serverless_framework_multiple_existing_functions():
    project_id = serverless_framework(
        "tests/dev/multiple-functions.py", do_cleanup=False
    )
    serverless_framework(
        "tests/dev/multiple-functions.py", do_cleanup=True, project_id=project_id
    )


def test_integration_serverless_framework_one_existing_function():
    project_id = serverless_framework("tests/dev/app.py", do_cleanup=False)
    serverless_framework(
        "tests/dev/multiple-functions.py", do_cleanup=True, project_id=project_id
    )
