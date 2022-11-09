from abc import ABC, abstractmethod
from typing import Optional

from scw_serverless.app import Serverless
from scw_serverless.logger import get_logger


class DeployConfig:
    def __init__(
        self,
        project_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: Optional[str] = None,
    ):
        self.project_id = project_id
        self.secret_key = secret_key
        self.region = region


class ServerlessBackend(ABC):
    def __init__(self, app_instance: Serverless, deploy_config: DeployConfig):
        self.app_instance = app_instance
        self.deploy_config = deploy_config
        self.logger = get_logger()

    @abstractmethod
    def deploy(self):
        pass
