"""Connectors classes"""
from abc import ABC, abstractmethod
from typing import Generator

import psycopg2
import pyexasol

from revlibs.connections.config import Config
from revlibs.connections.exceptions import ConnectionEstablishError, ConnectionParamsError


class BaseConnector(ABC):
    """Base class for connectors"""

    def __init__(self, cfg: Config) -> None:
        self.config = cfg
        self.connection = None

    @staticmethod
    @abstractmethod
    def _connect(config: Config):
        """Establish connection with database"""
        pass

    @staticmethod
    @abstractmethod
    def _is_connection_closed(connection) -> bool:
        """Check if connection with database closed already"""
        pass

    def is_connected(self) -> bool:
        """Check if connection with database established and not closed"""
        return bool(self.connection and not self._is_connection_closed(self.connection))

    def get_connection(self):
        """Open new DB connection or return already established if its not closed"""
        if self.is_connected():
            return self.connection
        self.connection = self._connect(self.config)
        return self.connection

    def close(self) -> None:
        """Close connection to database"""
        if not self.connection:
            return
        self.connection.close()
        self.connection = None


class ExasolConnector(BaseConnector):
    """Connector class for Exasol DB"""

    @staticmethod
    def _is_connection_closed(connection: pyexasol.ExaConnection) -> bool:
        """Check if connection with database closed already"""
        return connection.is_closed

    @staticmethod
    def _connect(config: Config) -> pyexasol.ExaConnection:
        """Establish connection with exasol"""
        params = {"compression": True}
        if "schema" in config:
            params["schema"] = config.schema
        params.update(config.params)

        try:
            return pyexasol.connect(
                dsn=config.dsn,
                user=config.user,
                password=config.password,
                fetch_dict=True,
                fetch_mapper=pyexasol.exasol_mapper,
                **params,
            )
        except pyexasol.exceptions.ExaConnectionDsnError as exc:
            raise ConnectionEstablishError(config.name, reason="Bad dsn", dsn=config.dsn) from exc
        except pyexasol.exceptions.ExaAuthError as exc:
            raise ConnectionEstablishError(
                config.name, reason="Authentication failed", dsn=config.dsn, user=config.user,
            ) from exc
        except pyexasol.exceptions.ExaConnectionFailedError as exc:
            raise ConnectionEstablishError(
                config.name, reason="Connection refused", dsn=config.dsn,
            ) from exc
        except pyexasol.exceptions.ExaError as exc:
            raise ConnectionEstablishError(config.name, dsn=config.dsn) from exc


class PostgresConnector(BaseConnector):
    """Connector class for PostgreSQL DB"""

    @staticmethod
    def _is_connection_closed(connection: psycopg2.extensions.connection) -> bool:
        """Check if connection with database closed already"""
        return connection.closed

    @staticmethod
    def _parse_dsn(data_source_name: str) -> Generator[str, None, None]:
        """Convert connection URI to key/value connection string.

        >>> list(PostgresConnector._parse_dsn('localhost:8888, 127.0.0.1:6543'))
        ['host=localhost port=8888', 'host=127.0.0.1 port=6543']
        """
        dsns = data_source_name.split(",")
        for dsn in dsns:
            host, port = dsn.strip().split(":")
            yield f"host={host} port={port}"

    @staticmethod
    def _connect(config: Config) -> psycopg2.extensions.connection:
        """Establish connection with postgres"""
        dbname = config.dbname if "dbname" in config else None

        connection, last_exception = None, None
        for dsn in PostgresConnector._parse_dsn(config.dsn):
            try:
                connection = psycopg2.connect(
                    dsn,
                    user=config.user,
                    password=config.password,
                    dbname=dbname,
                    **config.params,
                )
            except psycopg2.Error as exc:
                last_exception = exc

        if not connection:
            raise ConnectionEstablishError(
                config.name, dsn=config.dsn, user=config.user, dbname=dbname,
            ) from last_exception

        return connection
