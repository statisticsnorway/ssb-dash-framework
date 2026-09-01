from pydantic import BaseModel


class InfoRowField(BaseModel):
    """Model for a info field in the DataEditorInfoRow module."""

    name: str
    source: str
    source_variable_name: str

    def __str__(self) -> str:
        """String representation for InfoRowField."""
        return f"name: {self.name}\nsource: {self.source}\nsource_variable_name: {self.source_variable_name}"
