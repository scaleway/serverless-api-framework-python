import subprocess

from scw_serverless.app import Serverless
from scw_serverless.config.generators.serverlessframework import (
    ServerlessFrameworkGenerator,
)
from scw_serverless.deploy.backends.serverless_backend import (
    ServerlessBackend,
    DeployConfig,
)
from scw_serverless.utils.commands import get_command_path


class ServerlessFrameworkBackend(ServerlessBackend):
    def __init__(self, app_instance: Serverless, deploy_config: DeployConfig):
        super().__init__(app_instance, deploy_config)

    def deploy(self):
        # Generate the serverless.yml configuration
        serverless_framework_generator = ServerlessFrameworkGenerator(self.app_instance)
        serverless_framework_generator.write("./")

        # Test if nodejs is installed on the user's system
        node_path = get_command_path("node")
        if not node_path:
            raise RuntimeError("nodejs is not installed on your system")

        # Test if the serverless framework is installed on the user's system
        serverlessfw_path = get_command_path("serverless")
        if not serverlessfw_path:
            raise RuntimeError(
                "The serverless framework is not installed on your system"
            )

        # Call the serverless framework to perform the deployment
        subprocess.run(
            [
                node_path,
                serverlessfw_path,
                "deploy",
            ],
            env={
                "SCW_SECRET_KEY": self.deploy_config.secret_key,
                "SCW_DEFAULT_PROJECT_ID": self.deploy_config.project_id,
                "SCW_REGION": self.deploy_config.region,
            },
            cwd="./",
        )
