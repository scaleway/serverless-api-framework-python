import subprocess

from scw_serverless.config.generators.serverless_framework import (
    ServerlessFrameworkGenerator,
)
from scw_serverless.deploy.backends.serverless_backend import ServerlessBackend
from scw_serverless.utils.commands import get_command_path


class ServerlessFrameworkBackend(ServerlessBackend):
    """Uses ServerlessFramework to deploy functions."""

    def deploy(self):
        # Generate the serverless.yml configuration
        serverless_framework_generator = ServerlessFrameworkGenerator(self.app_instance)
        serverless_framework_generator.write("./")

        # Test if nodejs is installed on the user's system
        node_path = get_command_path("node")

        # Test if the serverless framework is installed on the user's system
        serverlessfw_path = get_command_path("serverless")

        secret_key = self.sdk_profile.secret_key
        project_id = self.sdk_profile.default_project_id
        region = self.sdk_profile.default_region
        if not secret_key or not project_id or not region:
            # While it won't happen under the normal control flow,
            # this prevents mypy errors
            raise RuntimeError("Invalid config")

        # Call the serverless framework to perform the deployment
        subprocess.run(
            [
                node_path,
                serverlessfw_path,
                "deploy",
            ],
            env={
                "SCW_SECRET_KEY": secret_key,
                "SCW_DEFAULT_PROJECT_ID": project_id,
                "SCW_REGION": region,
            },
            cwd="./",
            check=True,
        )

        self.logger.success("Done! Functions have been successfully deployed!")
