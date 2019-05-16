from setuptools import setup, find_packages

setup(
    name="revlibs-logger",
    version="0.3.3",
    author="Demeter Sztanko",
    author_email="demeter.sztanko@revolut.com",
    packages=find_packages(),
    package_data={"logger": ["logging.yaml"]},
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "pyaml>=18.11.0",
    ],
    extras_require={
        "slack": ["slacker-log-handler>=1.7.1"],
        "stackdriver": ["google-cloud-logging>=1.10.0"],
    },
    namespace_packages=["revlibs"],
)
