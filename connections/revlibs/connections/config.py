""" Handles the connection config."""
import os
import logging
from pathlib import Path

from revlibs.dicts import DictLoader


_DEFAULT_DIRECTORY = Path.home() / ".revconnect/"
_ENV_VAR_FOR_FILE = "REVLIB_CONNECTIONS"
_PASSWORD_REQUIRED = (
    # Provide a meaningful message
    "Please ensure you have set the password as an environment variable"
)


def load(database):
    """ Load the database connection configuration."""
    loader = load_connection_settings()
    candidates = [
        item
        for item in loader.items
        if database == item["name"] and item.get("disabled", False) is not True
    ]

    if len(candidates) == 1:
        db_config, *_ = candidates
    elif len(candidates) > 1:
        logging.error("Duplicate connection name '%s'.", database)
        raise KeyError(f"Duplicates for '{database}' found.")
    else:
        logging.error(f"No config for db called: '%s'.", database)
        raise KeyError(f"Connection settings for '{database}' not found.")

    return Config(database, db_config)


class Config:
    """Connection config."""

    def __init__(self, name, config):
        self.name = name
        self.config = config

    def __repr__(self):
        """ Print the config. Will not print secrets if they
        are not contained in the connection file.
        """
        return repr(self.config)

    def __contains__(self, item):
        """ Determine if config has an attr."""
        return item in self.config.keys()

    @property
    def params(self):
        """ Additional parameters to pass to the db connection."""
        return self.config["params"] if ("params" in self.config) else {}

    @property
    def password(self):
        """ Enforce retrieving password from environment."""
        result = self.config["password"]
        var_split = result.split(":", 2)
        try:
            env_name = var_split[1]
            return os.environ[env_name]
        except (KeyError, IndexError) as err:
            raise KeyError(_PASSWORD_REQUIRED)

    def __getattr__(self, key):
        """ Get attr from environment, if not set return default."""
        if key not in self.config:
            raise NameError(f"Database flavour requires '{key}'.")

        result = self.config[key]
        if isinstance(result, str) and result.startswith("_env"):
            var_split = result.split(":", 2)
            var_name = var_split[1]
            var_default = "" if len(var_split) < 3 else var_split[2]
            result = os.environ.get(var_name, var_default)
        return result


def load_connection_settings():
    """ Retrieve connections from specified yaml."""
    directory = Path(os.environ.get(_ENV_VAR_FOR_FILE, _DEFAULT_DIRECTORY))
    loader = DictLoader.from_path(directory)
    return loader
