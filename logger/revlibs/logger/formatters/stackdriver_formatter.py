from typing import List

import logging
import socket
import os
from pkgutil import get_data

from google.cloud.logging.handlers import CloudLoggingHandler
from google.cloud.logging import Client


def supported_keys() -> List[str]:
    """
    Get supported keys from the package resources
    """
    data = get_data("revlibs.logger", "resources/supported_keys")
    if data:
        return data.decode("utf-8").splitlines()


class StackdriverJsonFormatter(logging.Formatter):
    """
    Creates a `dict` to send a JSON object to StackDriver
    """

    _SUPPORTED_KEYS_ = supported_keys()

    def __init__(self):
        """
        Adds app environment info to the logger
        """
        super().__init__()
        self._enviroment_info_ = StackdriverJsonFormatter.environment_info()

    @staticmethod
    def environment_info():
        return {"hostname": socket.gethostname(), "user": os.environ.get("USER", "")}

    def format(self, record):
        """
        Creates dict out of the records, by populating only the fields specified in resources/supported_keys
        Apart from this, some variables on execution environment are added as well
        """
        record_dict = vars(record)
        text = record_dict.get("message", "")

        out = {k: serialize(v) for k, v in record_dict.items() if k in self._SUPPORTED_KEYS_}

        return {"text": text, "params": out, "environment": self._enviroment_info_}


def serialize(obj):
    """
    Serializes an object to be sent to StackDriver, defaulting to `str`
    """
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [serialize(v) for v in obj]

    if isinstance(obj, (str, int, float)):
        return obj

    return str(obj)


def add_stack_driver_support(log):
    client = Client()
    handler = client.get_default_handler()
    handler.setFormatter(StackdriverJsonFormatter())
    log.addHandler(handler)
