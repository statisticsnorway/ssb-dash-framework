from abc import ABC

from ...setup.variableselector import VariableSelector


class AltinnComponentBaseClass(ABC):
    def __init__(self, conn, variable_selector_instance):
        """Initializes the base class for Altinn components.

        Args:
            conn (DatabaseConnection): Database connection object that must have a 'query' method.
            variable_selector_instance (VariableSelector): An instance of VariableSelector for variable selection.

        Raises:
            TypeError: If variable_selector_instance is not an instance of VariableSelector.
        """
        assert hasattr(conn, "query"), "The database object must have a 'query' method."
        self.conn = conn
        if not isinstance(variable_selector_instance, VariableSelector):
            raise TypeError(
                "variable_selector_instance must be an instance of VariableSelector"
            )
        self.variable_selector = variable_selector_instance
