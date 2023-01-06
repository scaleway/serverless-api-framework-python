from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import yaml

DEFAULT_CONFIG_PATH = "~/.config/scw/py_api.yaml"


@dataclass
class Config:
    """Utility class to hold configuration parameters."""

    api_gw_host: Optional[str] = None  # Host for the API Gateway controller api
    gateway_id: Optional[str] = None  # Default API Gateway uuid

    def update_from_config_file(self, config_path: Optional[str] = None) -> "Config":
        """Update an existing config instance whith values passed via a config file."""
        config_path = config_path if config_path else DEFAULT_CONFIG_PATH
        config_path = Path(DEFAULT_CONFIG_PATH).expanduser()

        if not config_path.exists():
            return self

        with open(config_path, mode="rt", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            config |= asdict(self)
            return Config(**config)

        return self
