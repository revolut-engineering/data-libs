""" Test connection library."""
from pathlib import Path
from unittest.mock import patch
from unittest.mock import call
from unittest.mock import MagicMock

import pytest
import psycopg2
import pyexasol

from revlibs.connections import get, get_connector
from revlibs.connections.exceptions import ConnectionEstablishError, ConnectionParamsError


# Environment variables are strings by default
TEST_CONNECTIONS = Path(__name__).parent / "resources" / "test_connections/"
TEST_ENVIRONMENT = {
    "REVLIB_CONNECTIONS": TEST_CONNECTIONS.as_posix(),
    "TEST_PASS": "IamAwizard",
}


class ConnectionMock(MagicMock):
    """ Mock connection objects."""


@patch.dict("os.environ", TEST_ENVIRONMENT)
def test_simple_postgres():
    """ Test connection to postgres."""
    with patch("psycopg2.connect") as mocked_conn:

        with get("postgres_simple") as conn:
            pass

    mocked_conn.assert_called_with(
        "host=127.0.0.1 port=5436", dbname=None, password="IamAwizard", user="test"
    )
    conn.close.assert_called()


@patch.dict("os.environ", TEST_ENVIRONMENT)
def test_multi_server_postgres():
    """ First host:port fails, handle failover."""
    with patch("psycopg2.connect") as mocked_conn:
        mocked_conn.side_effect = [psycopg2.OperationalError, ConnectionMock()]

        with get("postgres_multi_server") as conn:
            pass

    mocked_conn.assert_has_calls(
        [
            call("host=127.0.0.1 port=5436", dbname=None, password="IamAwizard", user="test",),
            call("host=127.0.0.2 port=5436", dbname=None, password="IamAwizard", user="test",),
        ]
    )
    conn.close.assert_called()


@patch.dict("os.environ", TEST_ENVIRONMENT)
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
        fetch_mapper=pyexasol.exasol_mapper,
    )
    conn.close.assert_called()


@patch.dict("os.environ", TEST_ENVIRONMENT)
def test_bad_dsn_exasol():
    """ Test passing exasol a bad dsn."""
    with pytest.raises(ConnectionEstablishError) as err:
        with get("exasol_bad_dsn"):
            pass

    assert str(err.value) == "Could not connect to exasol_bad_dsn: Bad dsn [dsn=bad_dsn:8888]"


@patch.dict("os.environ", TEST_ENVIRONMENT)
def test_disabled_connection():
    """ Disabled connections are not handled."""
    with pytest.raises(ConnectionParamsError) as err:
        with get("postgres_disabled"):
            pass

    assert str(err.value) == (
        "Could not connect to postgres_disabled: "
        "Connection settings for 'postgres_disabled' not found."
    )


@patch.dict("os.environ", TEST_ENVIRONMENT)
def test_failed_connection_postgres():
    """ First and second host:port fail, an ConnectionEstablishError is raised."""
    with pytest.raises(ConnectionEstablishError) as err:
        with patch("psycopg2.connect") as mocked_conn:
            mocked_conn.side_effect = [psycopg2.OperationalError, psycopg2.OperationalError]
            with get("postgres_multi_server"):
                pass

    assert str(err.value) == (
        "Could not connect to postgres_multi_server "
        "[dsn=127.0.0.1:5436,127.0.0.2:5436 user=test dbname=None]"
    )


@patch.dict("os.environ", TEST_ENVIRONMENT)
def test_pyexasol_exceptions():
    with patch("pyexasol.connect") as mocked_conn:
        mocked_conn.side_effect = [
            pyexasol.exceptions.ExaAuthError(None, None, None),
            pyexasol.exceptions.ExaConnectionFailedError(None, None),
            pyexasol.exceptions.ExaRuntimeError(None, None),
        ]

        with pytest.raises(ConnectionEstablishError) as err:
            get_connector("exasol_multi_server").get_connection()
        assert str(err.value) == (
            "Could not connect to exasol_multi_server: Authentication failed "
            "[dsn=127.0.0.1:5436,127.0.0.2:5437 user=test]"
        )

        with pytest.raises(ConnectionEstablishError) as err:
            get_connector("exasol_multi_server").get_connection()
        assert str(err.value) == (
            "Could not connect to exasol_multi_server: Connection refused "
            "[dsn=127.0.0.1:5436,127.0.0.2:5437]"
        )

        with pytest.raises(ConnectionEstablishError) as err:
            get_connector("exasol_multi_server").get_connection()
        assert str(err.value) == (
            "Could not connect to exasol_multi_server "
            "[dsn=127.0.0.1:5436,127.0.0.2:5437]"
        )


@patch.dict("os.environ", TEST_ENVIRONMENT)
def test_unknown_flavour():
    with pytest.raises(ConnectionParamsError) as err:
        get_connector("unknown_flavour").get_connection()

    assert str(err.value) == (
        "Could not connect to unknown_flavour: unsupported database type newdb"
    )


@patch.dict("os.environ", TEST_ENVIRONMENT)
def test_get_connector_same_connection():
    with patch("psycopg2.connect", **{"return_value.closed": False}) as mocked_conn:
        connector = get_connector("postgres_simple")

        conn = connector.get_connection()
        assert conn

        assert connector.get_connection() == conn
        mocked_conn.assert_called_once()

        connector.close()
        conn.close.assert_called()
        connector.close()
        conn.close.assert_called_once()


@patch.dict("os.environ", TEST_ENVIRONMENT)
def test_get_connector_closed_connection():
    with patch("pyexasol.connect") as mocked_conn:
        connector = get_connector("exasol_multi_server")
        conn = connector.get_connection()

        conn.is_closed = False
        connector.get_connection()

        conn.is_closed = True
        connector.get_connection()

        assert mocked_conn.call_count == 2
