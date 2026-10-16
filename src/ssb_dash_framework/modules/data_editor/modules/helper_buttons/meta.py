from abc import abstractmethod, ABC
from os import listdir
from typing import List

import pandas as pd
from pydantic import BaseModel
from pydantic import Field

class ContactInfo(BaseModel):
    """Model representing detailed contact details of a survey respondent.

    Attributes:
        ident: Respondent identifier (e.g. enterprise number).
        skjema: Active questionnaire form name.
        kontaktperson: Full name of the contact person.
        epost: Email address.
        telefon: Phone number.
        bekreftet_kontaktinfo: Confirmation state.
        kommentar_kontaktinfo: General contact comments.
        kommentar_krevende: Comments highlighting challenging follow-ups.
    """
    ident: str
    skjema: str
    kontaktperson: str | None
    epost: str | None
    telefon: str | None
    bekreftet_kontaktinfo: str | None
    kommentar_kontaktinfo: str | None
    kommentar_krevende: str | None

    @classmethod
    def empty(cls) -> "ContactInfo":
        """Blank instance for error/no-data fallback paths."""
        return cls(
            ident="",
            skjema="",
            kontaktperson=None,
            epost=None,
            telefon=None,
            bekreftet_kontaktinfo=None,
            kommentar_kontaktinfo=None,
            kommentar_krevende=None,
        )

class HelperButtonMeta(ABC):
    """Interface defining database capabilities for action helper button modals."""

    @abstractmethod
    def get_history(self, refnr: str, insert_toggle: bool | None = None) -> pd.DataFrame:
        """Retrieves editing history log for a specific unit submission.

        Args:
            refnr: Reference number.
            insert_toggle: Optional boolean switch to filter out initial insert rows.

        Returns:
            A pandas DataFrame with history details.
        """
        ...

    @abstractmethod
    def get_contact_info(self, refnr: str) -> ContactInfo:
        """Retrieves full contact person details for a submission reference number.

        Args:
            refnr: Reference number.

        Returns:
            A ContactInfo model populated with retrieved values.
        """
        ...
