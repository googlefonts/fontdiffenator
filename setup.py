import sys
from setuptools import setup, find_packages, Command
from distutils import log

setup(
    name='diffenator',
    version='0.0.2',
    author="Google Fonts Project Authors",
    description="Font regression tester for Google Fonts",
    url="https://github.com/googlefonts/diffenator",
    license="Apache Software License 2.0",
    package_dir={"": "Lib"},
    packages=find_packages("Lib"),
    entry_points={
        "console_scripts": [
            "diffenator = diffenator.__main__:main",
            "dumper = diffenator.dumper:main",
        ],
    },
    install_requires=[
        "fonttools>=3.4.0",
    ],
)
