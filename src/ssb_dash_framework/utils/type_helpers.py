from typing import Any
from typing import Protocol


class DatabaseConnection(Protocol):
    """A protocol that defines the expected interface for a database connection.

    This protocol is used to ensure that any database connection object passed
    to the AltinnEditorComment module has a 'query' method.

    Methods:
        query(*args, **kwargs) -> Any: A method to execute a query against the database.
    """

    def query(self, *args: Any, **kwargs: Any) -> Any:
        """Executes a query against the database."""
        ...
