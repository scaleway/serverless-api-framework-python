import subprocess


def get_command_path(command: str):
    which = subprocess.run(["which", command], capture_output=True)
    if which.returncode == 0:
        return str(which.stdout.decode("UTF-8")).strip()
    raise RuntimeError(f"Unable to find command {command}")
