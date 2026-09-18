from abc import abstractmethod, ABC
from os import listdir
from typing import List

import pandas as pd
from pydantic import BaseModel
from pydantic import Field

class ContactInfo(BaseModel):
    ident: str
    skjema: str
    kontaktperson: str
    epost: str
    telefon: str
    bekreftet_kontaktinfo: str
    kommentar_kontaktinfo: str
    kommentar_krevende: str

    @classmethod
    def empty(cls) -> "ContactInfo":
        """Blank instance for error/no-data fallback paths."""
        return cls(
            ident="",
            skjema="",
            kontaktperson="",
            epost="",
            telefon="",
            bekreftet_kontaktinfo="",
            kommentar_kontaktinfo="",
            kommentar_krevende="",
        )

class HelperButtonMeta(ABC):
    @abstractmethod
    def get_history(self, refnr: str, insert_toggle: bool | None = None) -> pd.DataFrame: ...

    @abstractmethod
    def get_contact_info(self, refnr: str) -> ContactInfo: ...
