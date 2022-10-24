import os

import tests.utils as test_utils
from scw_serverless.deploy.gateway.controller import GatewayController
from scw_serverless.api import Api

from ....dev.gateway import app


def test_gateway_controller_manage():
    api = Api(region="fr-par", secret_key=os.getenv("SCW_SECRET_KEY"))
    ctrl = GatewayController(app, api)

    ctrl.manage_routes()
