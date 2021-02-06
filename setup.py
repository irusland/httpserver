import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name="ihttpy",
    version="2.0.1",
    author="irusland",
    author_email="ruslansir@icloud.com",
    description="A http server with fluent interface decorators",
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
)
