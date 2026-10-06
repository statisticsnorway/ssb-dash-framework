from abc import abstractmethod, ABC
from typing import Literal

from pydantic import BaseModel

import pandas as pd


class RefnrStatus(BaseModel):
    """Model describing the status of a form reference number submission.

    Attributes:
        active: Boolean flag indicating if this submission is active.
        status: The working state of the form.
    """
    active: bool
    status: Literal["Under arbeid", "Ferdig", "Ubehandlet"]

class RefnrStatusExtended(RefnrStatus):
    skjema: str
    dato_mottatt: str
    refnr: str
    kommentar: str

class SidebarMeta[T](ABC):
    """Metadata interface defining database interaction capabilities for sidebar modules."""

    @abstractmethod
    def get_form_status(self, refnr: str) -> RefnrStatus | None:
        """Retrieves active and status state of the specified form.

        Args:
            refnr: Reference number of the submission.

        Returns:
            A RefnrStatus instance or None if not found.
        """
        ...

    @abstractmethod
    def get_refnrs_by_period_ident(
        self, settings: T, ident: str, period: str
    ) -> list[RefnrStatusExtended] | None:
        """Retrieves all submission reference numbers for a given respondent and period.

        Args:
            settings: Editor settings context.
            ident: Respondent identifier.
            period: Statistical period.

        Returns:
            A list containing submission records or None.
        """
        ...

    @abstractmethod
    def get_comment(self, refnr: str) -> str | None:
        """Retrieves the reception comment associated with a form reference number.

        Args:
            refnr: Reference number.

        Returns:
            The comment string, or None.
        """
        ...

    @abstractmethod
    def update_form_status(
        self, refnr: str, status_code: Literal["Under arbeid", "Ferdig", "Ubehandlet"]
    ) -> None:
        """Updates the processing status of a form.

        Args:
            refnr: Reference number.
            status_code: New status value.
        """
        ...

    @abstractmethod
    def update_form_active_status(self, refnr: str, value: bool) -> None:
        """Updates the active flag of a form submission.

        Args:
            refnr: Reference number.
            value: True if active, False otherwise.
        """
        ...

    @abstractmethod
    def update_form_reception_comment(self, refnr: str, comment: str) -> None:
        """Updates or saves a comment associated with a form reference number.

        Args:
            refnr: Reference number.
            comment: The comment text.
        """
        ...
