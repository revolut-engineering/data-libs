"""Standard connection interfaces"""
from contextlib import contextmanager
from typing import Iterator, Union

import psycopg2
import pyexasol

from revlibs.connections import config
from revlibs.connections.connectors import BaseConnector, ExasolConnector, PostgresConnector
from revlibs.connections.exceptions import ConnectionParamsError

CONNECTORS = {"exasol": ExasolConnector, "postgres": PostgresConnector}


def get_connector(name: str) -> BaseConnector:
    """Return connector object used for handling of connection.

    Database connection parameters will be loaded from YAML/JSON config stored
    in `~/.revconnect/` directory or another path specified by environment
    variable `REVLIB_CONNECTIONS`.

    Opened connection should always be closed when it's not needed anymore,
    using connector `close()` method or from connection (`connection.close()`)

    Connector object will store established database connection inside, so on
    first call of method `get_connection()` it will open new connection and on
    next calls it will be returning already established connection unless
    connection will be closed using its internal method (`connection.close()`)
    or through connector object method `close()`.

    Example::
        connector = get_connector("exasol_db")
        connection = connector.get_connection()  # open new connection
        connection.execute("SELECT * FROM table1;")
        connector.get_connection()  # return already established connection
        connection.close()
        connection = connector.get_connection()  # open new connection
        ...
        connector.close()  # close connection

    Raises:
        ConnectionParamsError: If connection params in config are invalid
        ConnectionEstablishError: If connection cannot be established
    """
    try:
        cfg = config.load(name)
    except KeyError as exc:
        raise ConnectionParamsError(name, reason=exc.args[0])

    try:
        connector_class = CONNECTORS[cfg.flavour]
    except KeyError:
        raise ConnectionParamsError(name, reason=f"unsupported database type {cfg.flavour}")

    return connector_class(cfg)


@contextmanager
def get(name: str) -> Iterator[Union[pyexasol.ExaConnection, psycopg2.extensions.connection]]:
    """Context manager that open connection to database and close it after.

    Database connection parameters will be loaded from YAML/JSON config stored
    in `~/.revconnect/` directory or another path specified by environment
    variable `REVLIB_CONNECTIONS`

    Example::
        with get("exasol_db") as connection:  # open new connection
            connection.execute("SELECT * FROM table1;")
        # connection will be closed here

    Raises:
        ConnectionParamsError: If connection params in config are invalid
        ConnectionEstablishError: If connection cannot be established
    """
    connector = get_connector(name)
    yield connector.get_connection()
    connector.close()
