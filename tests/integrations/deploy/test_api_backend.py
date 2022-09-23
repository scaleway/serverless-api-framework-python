from integrations.utils import deploy


def test_integration_deploy():
    deploy("tests/dev/app.py")


def test_integration_deploy_multiple_functions():
    deploy("tests/dev/multiple-functions.py")


def test_integration_deploy_existing_function():
    project_id = deploy("tests/dev/app.py", do_cleanup=False)
    deploy("tests/dev/app.py", do_cleanup=True, project_id=project_id)


def test_integration_deploy_multiple_existing_functions():
    project_id = deploy("tests/dev/multiple-functions.py", do_cleanup=False)
    deploy("tests/dev/multiple-functions.py", do_cleanup=True, project_id=project_id)


def test_integration_deploy_one_existing_function():
    project_id = deploy("tests/dev/app.py", do_cleanup=False)
    deploy("tests/dev/multiple-functions.py", do_cleanup=True, project_id=project_id)
