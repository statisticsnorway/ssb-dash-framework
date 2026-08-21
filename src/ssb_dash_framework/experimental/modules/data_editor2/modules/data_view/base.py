from abc import abstractmethod
from ...meta import ContextABC


class DataEditorDataView(ContextABC):
    """Base class for defining a data view."""


    def __init__(
        self, applies_to_tables: str | list[str], applies_to_forms: str | list[str]
    ) -> None:
        """Initializes and registers a DataEditorDataView module.

        Args:
            applies_to_tables: A list of tables in the database that this view should apply to.
            applies_to_forms: A list of forms that this view should apply to.¨

        Raises:
            TypeError: If not all tables and forms in applies_to_tables and applies_to_forms are strings.
        """
        if isinstance(applies_to_tables, str):
            applies_to_tables = [applies_to_tables]
        self.applies_to_tables = applies_to_tables
        if isinstance(applies_to_forms, str):
            applies_to_forms = [applies_to_forms]
        self.applies_to_forms = applies_to_forms

        for table in self.applies_to_tables:
            if not isinstance(table, str):
                raise TypeError(
                    f"Expected all tables to be strings. Received: '{table}' of type '{type(table)}'"
                )

    @abstractmethod
    def _create_layout(self) -> None:
        """Abstract method for creating the module layout."""
        pass

    def layout(self) -> None:
        """Returns the module layout."""
        return self._create_layout()

    @abstractmethod
    def module_callbacks(self) -> None:
        """Abstract method to register callbacks."""
        pass
