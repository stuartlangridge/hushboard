#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages


def get_long_description() -> str:
    with open("README.md", "r") as file:
        return file.read()


setup(
    name="hushboard",
    version="0.0.1",
    description="Mute your mic while you're typing.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Stuart Langridge",
    author_email="sil@kryogenix.org",
    license="MIT",
    url="https://github.com/stuartlangridge/hushboard",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": ["hushboard=hushboard.__main__:main"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
    ],
    extras_require={},
)
