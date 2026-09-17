from abc import abstractmethod, ABC
from os import listdir
from typing import List

import pandas as pd
from pydantic import BaseModel
from pydantic import Field

class ContactInfo(BaseModel):
    orgnr: str = ""
    skjema: str = ""
    kontaktperson: str = ""
    epost: str = ""
    tlf: str = ""
    bekreftet: list[bool] = Field(
        default_factory=list[bool],
        description="Whether the kontaktinfo in the Altinn3 survey was 'bekreftet', where str(1) = bekreftet.",
    )
    kommentar_kontaktinfo: str = ""
    kommentar_krevende: str = ""
    indicator_style: dict[str, str] = Field(
        default_factory=lambda: {"display": "none"},
        description="Show (or hide) indicator for when comment_count > 0.",
    )
    comment_count: str = Field(
        default="", description="Count of how many comments are filled out in the Altinn3 survey."
    )

    def as_dash_tuple(self) -> tuple:
        """Values in field-declaration order, matching the callback's Output order."""
        return tuple(self.model_dump().values())

class HelperButtonMeta(ABC):
    @abstractmethod
    def get_history(self, refnr: str, insert_toggle: bool | None = None) -> pd.DataFrame: ...

    @abstractmethod
    def get_contact_info(self, refnr: str) -> pd.DataFrame: ...
