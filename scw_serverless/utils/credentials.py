import os
from importlib.metadata import version
from typing import Optional

from scaleway import (
    Client,
    Profile,
    load_profile_from_config_file,
    load_profile_from_env,
)
from scaleway.core.profile.env import ENV_KEY_SCW_SECRET_KEY

from scw_serverless.logger import get_logger

DEFAULT_REGION: str = "fr-par"


def get_scw_profile(
    profile_name: Optional[str],
    secret_key: Optional[str],
    project_id: Optional[str],
    region: Optional[str],
) -> Profile:
    """Attempts to load the profile. Will raise on invalid profiles."""
    if profile_name or not os.getenv(ENV_KEY_SCW_SECRET_KEY):
        # pylint: disable=line-too-long
        get_logger().default(
            f'Using credentials from scw config with profile {profile_name or "default"}'
        )
        profile = load_profile_from_config_file(profile_name=profile_name)
        _update_profile_from_cli(profile, secret_key, project_id, region)
        _validate_profile(profile)
        return profile
    get_logger().default("Using credentials from system environment")
    profile = load_profile_from_env()
    _update_profile_from_cli(profile, secret_key, project_id, region)
    _validate_profile(profile)
    return profile


def _validate_profile(profile: Profile):
    """Validate a SDK profile to be used with scw_serverless."""
    client = Client.from_profile(profile)
    client.validate()  # Will throw
    if not profile.default_project_id:
        # Client.validate will have already checked that it's an uuid if it exists
        raise ValueError("Invalid config, default_project_id must be defined")


def _update_profile_from_cli(
    profile: Profile,
    secret_key: Optional[str],
    project_id: Optional[str],
    region: Optional[str],
):
    """Update values with defined CLI arguments."""
    profile.user_agent = f'scw-serverless/{version("scw_serverless")}'
    profile.secret_key = secret_key or profile.secret_key
    profile.default_project_id = project_id or profile.default_project_id
    profile.default_region = region or profile.default_region
    if not profile.default_region:
        profile.default_region = DEFAULT_REGION
        get_logger().info(f"No region was configured, using {profile.default_region}")
