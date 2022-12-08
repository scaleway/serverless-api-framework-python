import shutil


def get_command_path(command: str) -> str:
    """Gets the path of a command."""
    location = shutil.which(command)
    if not location:
        raise RuntimeError(f"Unable to find command {command}")
    return location
