""" Package setup."""
from setuptools import setup, find_packages

setup(
    name="revlibs-connections",
    version="0.2.0",
    author="Demeter Sztanko",
    author_email="demeter.sztanko@revolut.com",
    description="A utility to pre-configure connections regardless of type.",
    url="https://github.com/revolut-engineering/data-libs/tree/master/connections",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=["revlibs-dicts>=0.0.1", "psycopg2-binary>=2.8", "pyexasol>=0.12",],
    namespace_packages=["revlibs"],
)
