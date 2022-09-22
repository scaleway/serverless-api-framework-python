from abc import ABC, abstractmethod


class DeployConfig:
    def __init__(
        self, project_id: str = None, serect_key: str = None, region: str = None
    ):
        self.project_id = project_id
        self.secret_key = serect_key
        self.region = region


class ServerlessBackend(ABC):
    @abstractmethod
    def deploy(self, deploy_config: DeployConfig):
        pass
