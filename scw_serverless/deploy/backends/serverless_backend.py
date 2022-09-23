from abc import ABC, abstractmethod

from scw_serverless.app import Serverless
from scw_serverless.logger import get_logger


class DeployConfig:
    def __init__(
        self, project_id: str = None, serect_key: str = None, region: str = None
    ):
        self.project_id = project_id
        self.secret_key = serect_key
        self.region = region


class ServerlessBackend(ABC):

    def __init__(self, app_instance: Serverless):
        self.app_instance = app_instance
        self.logger = get_logger()

    @abstractmethod
    def deploy(self, deploy_config: DeployConfig):
        pass
