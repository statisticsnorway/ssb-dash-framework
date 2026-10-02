from abc import abstractmethod, ABC
from typing import Literal

from pydantic import BaseModel

from .info_row_model import InfoRowField


class RefnrStatus(BaseModel):
    """Model describing the status of a form reference number submission.

    Attributes:
        active: Boolean flag indicating if this submission is active.
        status: The working state of the form.
    """
    active: bool
    status: Literal["Under arbeid", "Ferdig", "Ubehandlet"]


class InforowMeta[T](ABC):
    """Metadata interface defining database interaction capabilities for the InfoRow module."""

    @abstractmethod
    def get_info_row_fields(
        self,
        settings: T,
        refnr: str,
        period: str,
        fields: list[InfoRowField],
        states: dict[str, dict]
    ) -> dict[str, str | int | bool | float | None]:
        """Queries and returns metadata values for the InfoRow fields.

        Args:
            settings: Editor settings context.
            refnr: Reference number.
            period: Statistical period.
            fields: List of metadata fields to query.
            states: Map of active VariableSelector state items.

        Returns:
            A dictionary mapping field names to their database values.
        """
        ...

