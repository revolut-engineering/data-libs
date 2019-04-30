""" Test configuration."""
from unittest.mock import patch

import pytest

from revlibs.connections.config import Config


def test_raise_password():
    """ Test config raises an error when password isnt grabbed from env."""
    config = Config("test", {"password": "wizards"})
    with pytest.raises(KeyError):
        config.password


@patch.dict("os.environ", {"GET_ME": "wizards"})
def test_password_fetched():
    """ Test config grabs password from env."""
    config = Config("test", {"password": "_env:GET_ME"})
    assert config.password == "wizards"
