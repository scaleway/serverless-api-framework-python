import subprocess

from scw_serverless.app import Serverless
from scw_serverless.config.generators.serverlessframework import (
    ServerlessFrameworkGenerator,
)
from scw_serverless.deploy.backends.serverless_backend import (
    ServerlessBackend,
    DeployConfig,
)
from scw_serverless.utils import check_if_installed


class ServerlessFrameworkBackend(ServerlessBackend):
    def __init__(self, app_instance: Serverless):
        self.app_instance = app_instance

    def deploy(self, deploy_config: DeployConfig):
        # Generate the serverless.yml configuration
        serverless_framework_generator = ServerlessFrameworkGenerator(self.app_instance)
        serverless_framework_generator.write("./")

        # Test if nodejs is installed on the user's system
        if not check_if_installed("node"):
            raise RuntimeError("nodejs is not installed on your system")

        # Test if the serverless framework is installed on the user's system
        if not check_if_installed("serverless"):
            raise RuntimeError(
                "The serverless framework is not installed on your system"
            )

        # Get serverless and node installation path
        serverless_which = subprocess.run(["which", "serverless"], capture_output=True)
        node_which = subprocess.run(["which", "node"], capture_output=True)

        # Call the serverless framework to perform the deployment
        subprocess.run(
            [
                str(node_which.stdout.decode("UTF-8")).strip(),
                str(serverless_which.stdout.decode("UTF-8")).strip(),
                "deploy",
            ],
            env={
                "SCW_SECRET_KEY": deploy_config.secret_key,
                "SCW_DEFAULT_PROJECT_ID": deploy_config.project_id,
                "SCW_REGION": deploy_config.region,
            },
            cwd="./",
        )
