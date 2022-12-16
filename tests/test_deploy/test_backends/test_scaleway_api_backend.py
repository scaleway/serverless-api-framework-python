from typing import Any
from unittest.mock import MagicMock

import pytest
import scaleway.function.v1beta1 as sdk

from scw_serverless.app import Serverless
from scw_serverless.config import Function
from scw_serverless.deploy.backends.scaleway_api_backend import ScalewayApiBackend
from scw_serverless.triggers import CronTrigger


@pytest.fixture(autouse=True)
def no_s3_upload(monkeypatch: Any):
    """Prevents requests.put from executing."""
    put = MagicMock()
    put.return_value.status_code = 200
    monkeypatch.setattr("requests.put", put)


@pytest.fixture(autouse=True)
def mock_pool_starmap(monkeypatch: Any):
    """Provides a simple starmap implementation which does not rely on pickling."""
    monkeypatch.setattr(
        "multiprocessing.pool.Pool.starmap",
        lambda self, func, args: [func(*arg) for arg in args],
    )


def test_scaleway_api_backend_deploy_function():
    function = Function(
        name="test-function",
        handler="handler",
        runtime=sdk.FunctionRuntime("python311"),
    )
    app = Serverless("test-namespace")
    app.functions = [function]
    backend = ScalewayApiBackend(app, MagicMock(), True)
    # This would otherwise create some massive side effects
    create_zip = MagicMock()
    create_zip.return_value = "300"
    backend._create_deployment_zip = create_zip

    api = MagicMock()
    namespace = MagicMock()
    # pylint: disable=invalid-name,attribute-defined-outside-init
    namespace.id = "namespace-id"
    namespace.status = sdk.NamespaceStatus.READY
    api.create_namespace.return_value = namespace
    api.wait_for_namespace.return_value = namespace

    deployed_func = MagicMock()
    deployed_func.name = function.name
    deployed_func.domain_name = "test-domain.fnc.fr-par.scw.cloud"
    deployed_func.status = sdk.FunctionStatus.READY
    api.wait_for_function.return_value = deployed_func

    backend.api = api
    backend.deploy()

    backend.api.create_function.assert_called_once()
    args = backend.api.create_function.call_args.kwargs
    assert args["name"] == function.name


def test_scaleway_api_backend_deploy_function_with_trigger():
    trigger = CronTrigger(
        schedule="* * * * * *",
        name="test-cron",
    )
    function = Function(
        name="test-function-with-trigger",
        handler="handler",
        runtime=sdk.FunctionRuntime("python311"),
        triggers=[trigger],
    )
    app = Serverless("test-namespace")
    app.functions = [function]
    backend = ScalewayApiBackend(app, MagicMock(), True)
    # This would otherwise create some massive side effects
    create_zip = MagicMock()
    create_zip.return_value = "300"
    backend._create_deployment_zip = create_zip

    api = MagicMock()
    namespace = MagicMock()
    # pylint: disable=invalid-name,attribute-defined-outside-init
    namespace.id = "namespace-id"
    namespace.status = sdk.NamespaceStatus.READY
    api.create_namespace.return_value = namespace
    api.wait_for_namespace.return_value = namespace

    deployed_func = MagicMock()
    deployed_func.name = function.name
    deployed_func.id = function.name
    deployed_func.domain_name = "test-domain.fnc.fr-par.scw.cloud"
    deployed_func.status = sdk.FunctionStatus.READY
    api.wait_for_function.return_value = deployed_func

    backend.api = api
    backend.deploy()

    backend.api.create_function.assert_called_once()
    args = backend.api.create_function.call_args.kwargs
    assert args["name"] == function.name

    backend.api.create_cron.assert_called_once_with(
        function_id=deployed_func.id, schedule=trigger.schedule, name=trigger.name
    )
