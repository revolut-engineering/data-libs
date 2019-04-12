""" Package setup."""
from setuptools import setup, find_packages

setup(
    name="revlibs-connections",
    version="0.0.4",
    author="Demeter Sztanko",
    author_email="demeter.sztanko@revolut.com",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "revlibs-dicts>=0.0.1",
        "revlibs-logger>=0.0.2",
        "psycopg2-binary>=2.8",
        "pyexasol>=0.5.2",
    ],
    namespace_packages=["revlibs"],
)
