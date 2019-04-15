""" Test connection library."""
from pathlib import Path
from unittest.mock import patch
from unittest.mock import call
from unittest.mock import MagicMock

import pytest
import psycopg2
import pyexasol

from revlibs.connections import get


# Environment variables are strings by default
TEST_CONNECTIONS = Path(__name__).parent / "resources" / "test_connections/"
TEST_EVIRONMENT = {
    "REVLIB_CONNECTIONS": TEST_CONNECTIONS.as_posix(),
    "TEST_PASS": "IamAwizard",
}


class ConnectionMock(MagicMock):
    """ Mock connection objects."""


@patch.dict("os.environ", TEST_EVIRONMENT)
def test_simple_postgres():
    """ Test connection to postgres."""
    with patch("psycopg2.connect") as mocked_conn:

        with get("postgres_simple") as conn:
            pass

    mocked_conn.assert_called_with(
        "host=127.0.0.1 port=5436", dbname=None, password="IamAwizard", user="test"
    )
    conn.close.assert_called()


@patch.dict("os.environ", TEST_EVIRONMENT)
def test_multi_server_postgres():
    """ First host:port fails, handle failover."""
    with patch("psycopg2.connect") as mocked_conn:
        mocked_conn.side_effect = [psycopg2.OperationalError, ConnectionMock()]

        with get("postgres_multi_server") as conn:
            pass

    mocked_conn.assert_has_calls(
        [
            call(
                "host=127.0.0.1 port=5436",
                dbname=None,
                password="IamAwizard",
                user="test",
            ),
            call(
                "host=127.0.0.2 port=5436",
                dbname=None,
                password="IamAwizard",
                user="test",
            ),
        ]
    )
    conn.close.assert_called()


@patch.dict("os.environ", TEST_EVIRONMENT)
def test_multi_server_exasol():
    """ Test passing exasol multiple connections."""
    with patch("pyexasol.connect") as mocked_conn:
        with get("exasol_multi_server") as conn:
            pass

    mocked_conn.assert_called_with(
        compression=True,
        dsn="127.0.0.1:5436,127.0.0.2:5437",
        fetch_dict=True,
        password="IamAwizard",
        schema="s",
        user="test",
        fetch_mapper=pyexasol.exasol_mapper
    )
    conn.close.assert_called()


@patch.dict("os.environ", TEST_EVIRONMENT)
def test_bad_dsn_exasol():
    """ Test passing exasol a bad dsn."""
    with pytest.raises(pyexasol.exceptions.ExaCommunicationError):
        with get("exasol_bad_dsn"):
            pass


def test_disabled_connection():
    """ Disabled connections are not handled."""
    with pytest.raises(KeyError):
        with get("postgres_disabled") as connection:
            assert not connection
