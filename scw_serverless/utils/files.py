import os
from zipfile import ZipFile


def list_files(source: str) -> list[str]:
    """Lists files contained in the source directory."""

    zip_files = []

    for path, _subdirs, files in os.walk(source):
        for name in files:
            zip_files.append(os.path.join(path, name))

    return zip_files


def create_zip_file(zip_path: str, source: str) -> None:
    """Creates an archive to zip_path from source."""

    files = list_files(source)

    with ZipFile(zip_path, "w", strict_timestamps=False) as zip_file:
        for file in files:
            zip_file.write(file)
