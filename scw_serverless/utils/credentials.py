from importlib.metadata import version
from typing import Optional

from scaleway import Client
from scaleway_core.bridge.region import REGION_FR_PAR

from scw_serverless.logger import get_logger

DEFAULT_REGION: str = REGION_FR_PAR


def get_scw_client(
    profile_name: Optional[str],
    secret_key: Optional[str],
    project_id: Optional[str],
    region: Optional[str],
) -> Client:
    """Attempts to load the profile. Will raise on invalid profiles."""
    client = Client.from_config_file_and_env(profile_name)
    _update_client_from_cli(client, secret_key, project_id, region)
    return _validate_client(client)


def _validate_client(client: Client) -> Client:
    """Validate a SDK profile to be used with scw_serverless.
    Note: because we do not specify the project_id in API calls,
    it needs to be defined in the client.
    """
    client.validate()  # Will throw
    if not client.default_project_id:
        # Client.validate will have already checked that it's an uuid if it exists
        raise ValueError("Invalid config, project_id must be specified")
    return client


def _update_client_from_cli(
    client: Client,
    secret_key: Optional[str],
    project_id: Optional[str],
    region: Optional[str],
):
    """Update Client with defined CLI arguments."""
    client.user_agent = f'scw-serverless/{version("scw_serverless")}'
    client.secret_key = secret_key or client.secret_key
    client.default_project_id = project_id or client.default_project_id
    client.default_region = region or client.default_region
    if not client.default_region:
        get_logger().info(f"No region was configured, using {DEFAULT_REGION}")
        client.default_region = DEFAULT_REGION
