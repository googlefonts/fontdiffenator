import sys
from setuptools import setup, find_packages, Command
from distutils import log

setup(
    name='fontdiffenator',
    version='0.4.4',
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
        "fonttools>=3.28.0",
    ],
)
