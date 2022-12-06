from abc import ABC, abstractmethod

from scaleway import Profile

from scw_serverless.app import Serverless
from scw_serverless.logger import get_logger


class ServerlessBackend(ABC):
    """Backend to deploy functions with."""

    def __init__(self, app_instance: Serverless, sdk_profile: Profile):
        self.app_instance = app_instance
        self.sdk_profile = sdk_profile
        self.logger = get_logger()

    @abstractmethod
    def deploy(self):
        """Deploy the functions defined in app_instance."""
