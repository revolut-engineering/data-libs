"""Definitions of exceptions raised by connections library"""


class DatabaseConnectionError(Exception):
    """Base exception for problems with establishment of database connection"""

    def __init__(self, connection_name: str, reason: str = "", **kwargs) -> None:
        self.message = f"Could not connect to {connection_name}"
        if reason:
            self.message = f"{self.message}: {reason}"
        if kwargs:
            params = " ".join(f"{k}={v}" for k, v in kwargs.items())
            self.message = f"{self.message} [{params}]"

        super().__init__(self.message)


class ConnectionParamsError(DatabaseConnectionError):
    """Raised when there is a problem with connection params"""


class ConnectionEstablishError(DatabaseConnectionError):
    """Raised when connection to database cannot be established"""
