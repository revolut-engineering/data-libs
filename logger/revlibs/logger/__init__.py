from typing import Union

import logging
import logging.config

from os import environ, _Environ
from pkgutil import get_data

import yaml

from .formatters import color_formatter


DEFAULTS = {
    "LOG_FILE_LOCATION": "/tmp/python-log.log",
    "LOG_ROTATING_INTERVAL": "h",
    # "APP_NAME": "Python application",
    "LOG_LEVEL_CONSOLE": "INFO",
    "LOG_LEVEL_FILE": "DEBUG",
    "LOG_SLACK_USER": "Logger",
    "DEFAULT_SLACK_CHANNEL": "NOT_SET",
    "LOG_SLACK_TOKEN": "NOT_SET",  # This should be overridden, otherwise message will not be sent
}
STACKDRIVER_LOGGING_ENABLE_VAR = "STACKDRIVER_LOGGING_ENABLE"
LOGGING_CONFIG_LOCATION = environ.get("LOG_CONFIG_PATH")


def _load_logging_config_(params):

    params.update({k: v for k, v in DEFAULTS.items() if k not in params})

    if LOGGING_CONFIG_LOCATION:
        with open(LOGGING_CONFIG_LOCATION) as f:
            config_str = f.read()
    else:
        config_data = get_data("revlibs.logger", "resources/logging.yaml")
        if config_data:
            config_str = config_data.decode("utf-8")
        else:
            raise Exception("Could not find default logging.yaml")
    return yaml.load(config_str.format(**params), Loader=yaml.Loader)


def select_handlers(names, config):
    """ This filters out the handlers specified in log config."""
    handlers = config['handlers'].copy()
    for handler_name in handlers.keys():
        if handler_name not in names:
            config['handlers'].pop(handler_name)

    if 'slack' not in names:
        config['loggers'].pop('slack')

    return config


def get_logger(name=None, params: Union[dict, _Environ] = None, add_handlers=["console", "file"]):
    """
    Initialise the logger using the logging.yaml template
    Use environ() where no parameters are specified

    Logs to 'console' and 'file' by default.
    """
    if not params:
        params = environ

    config = _load_logging_config_(params)
    config = select_handlers(add_handlers, config)
    logging.config.dictConfig(config)
    log = logging.getLogger(name)

    # Add stackdriver handler
    if 'stackdriver' in add_handlers:
        from .formatters import stackdriver_formatter

        log.info("STACKDRIVER enabled")
        stackdriver_formatter.add_stack_driver_support(log)

    return log
