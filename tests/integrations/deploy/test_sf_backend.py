from tests.integrations.utils import deploy


def test_integration_deploy_using_srvless_fw():
    deploy("tests/dev/app.py", backend="serverless")


def test_integration_deploy_multiple_functions_using_srvless_fw():
    deploy("tests/dev/multiple-functions.py", backend="serverless")


def test_integration_deploy_existing_function_using_srvless_fw():
    project_id = deploy("tests/dev/app.py", do_cleanup=False, backend="serverless")
    deploy(
        "tests/dev/app.py", do_cleanup=True, project_id=project_id, backend="serverless"
    )


def test_integration_deploy_multiple_existing_functions_using_srvless_fw():
    project_id = deploy(
        "tests/dev/multiple-functions.py", do_cleanup=False, backend="serverless"
    )
    deploy(
        "tests/dev/multiple-functions.py",
        do_cleanup=True,
        project_id=project_id,
        backend="serverless",
    )


def test_integration_deploy_one_existing_function_using_srvless_fw():
    project_id = deploy("tests/dev/app.py", do_cleanup=False, backend="serverless")
    deploy(
        "tests/dev/multiple-functions.py",
        do_cleanup=True,
        project_id=project_id,
        backend="serverless",
    )
