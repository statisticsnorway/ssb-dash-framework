from abc import abstractmethod, ABC
from typing import Literal

from pydantic import BaseModel

from .info_row_model import InfoRowField


class RefnrStatus(BaseModel):
    active: bool
    status: Literal["Under arbeid", "Ferdig", "Ubehandlet"]


class InforowMeta[T](ABC):
    @abstractmethod
    def get_info_row_fields(
        self,
        settings: T,
        ident: str,
        period: str,
        fields: list[InfoRowField],
    ) -> dict[str, str | int | bool | float | None]: ...

