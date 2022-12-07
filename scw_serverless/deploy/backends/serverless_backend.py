from abc import ABC, abstractmethod

from scaleway import Client

from scw_serverless.app import Serverless
from scw_serverless.logger import get_logger


class ServerlessBackend(ABC):
    """Backend to deploy functions with."""

    def __init__(self, app_instance: Serverless, sdk_client: Client):
        self.app_instance = app_instance
        self.sdk_client = sdk_client
        self.logger = get_logger()

    @abstractmethod
    def deploy(self) -> None:
        """Deploy the functions defined in app_instance."""
