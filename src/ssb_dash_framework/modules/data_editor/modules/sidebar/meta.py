from abc import abstractmethod, ABC
from typing import Any, Literal

from pydantic import BaseModel

import pandas as pd


class RefnrStatus(BaseModel):
    active: bool
    status: Literal["Under arbeid", "Ferdig", "Ubehandlet"]


class SidebarMeta[T](ABC):
    @abstractmethod
    def get_form_status(self, refnr: str) -> RefnrStatus | None: ...

    @abstractmethod
    def get_refnrs_by_period_ident(
        self, settings: T, ident: str, period: str
    ) -> pd.DataFrame | None: ...

    @abstractmethod
    def get_comment(self, refnr: str) -> str | None: ...

    @abstractmethod
    def update_form_status(self, refnr: str, status_code: Any) -> None:
        ...

    @abstractmethod
    def update_form_active_status(self, refnr: str, value: bool) -> None:
        ...
    
    @abstractmethod
    def update_form_reception_comment(self, refnr: str, comment: str) -> None:
        ...