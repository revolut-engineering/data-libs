from setuptools import setup, find_packages

setup(
    name="revlibs-dicts",
    version="0.1.1",
    author="Demeter Sztanko",
    author_email="demeter.sztanko@revolut.com",
    description="An API for manipulating lists of dictionaries.",
    url="https://github.com/revolut-engineering/data-libs/tree/master/dicts",
    py_modules=["revlibs.dicts"],
    python_requires=">=3.6",
    install_requires=["ruamel.yaml>=0.15.89"],
    namespace_packages=["revlibs"],
)
