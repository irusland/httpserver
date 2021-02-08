import os
import sys

import setuptools
from setuptools.command.install import install


VERSION = '2.0.5'


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}"\
                .format(tag, VERSION)
            sys.exit(info)


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()


setuptools.setup(
    name="ihttpy",
    version=VERSION,
    author="irusland",
    author_email="ruslansir@icloud.com",
    description="A http server with fluent interface decorators, and plain "
                "text configuration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/irusland/httpserver",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    install_requires=required,
    cmdclass={
        'verify': VerifyVersionCommand,
    }
)
