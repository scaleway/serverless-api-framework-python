#!/usr/bin/env python
from setuptools import setup, find_packages

install_requires = ["click==8.1.3", "PyYAML==6.0", "setuptools", "requests==2.28.1"]

setup(
    name="serverless",
    version="0.0.1",
    install_requires=install_requires,
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"serverless": ["*.py", "*.yml"]},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "srvlss = serverless.cli:main",
        ]
    },
)
