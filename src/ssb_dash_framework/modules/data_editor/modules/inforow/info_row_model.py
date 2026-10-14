from pydantic import BaseModel


class InfoRowField(BaseModel):
    """Model representing an informational metadata card field in the InfoRow.

    Attributes:
        name: Header label displaying the property name (e.g. "Name" or "Org. Nr.").
        source: Auxiliary database table to query (e.g. "enhetsinfo") or "variableselector".
        source_variable_name: The column or variable key name inside the source table.
    """

    name: str
    source: str
    source_variable_name: str

    def __str__(self) -> str:
        """String representation for InfoRowField."""
        return f"name: {self.name}\nsource: {self.source}\nsource_variable_name: {self.source_variable_name}"
