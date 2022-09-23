import os
from zipfile import ZipFile


def list_files(source):
    zip_files = []

    for path, subdirs, files in os.walk(source):
        for name in files:
            zip_files.append(os.path.join(path, name))

    return zip_files


def create_zip_file(zip_path, source):
    files = list_files(source)

    with ZipFile(zip_path, "w", strict_timestamps=False) as zip:
        for file in files:
            zip.write(file)
