from abc import abstractmethod, ABC
from typing import Any

from .microlayout_components.editable_field_model import FieldCallbackContainer

class MicrolayoutMeta[T](ABC):
    @abstractmethod
    def get_field(
        self,
        settings: T,
        container: FieldCallbackContainer,
        inputs: list[Any] | dict[Any, Any],
    ) -> Any: ...

    @abstractmethod
    def get_timeseries(
        self,
        settings: T,
        variable: str | list[str],
        refnr: str,
        ident: str,
        periods: list[str],
    ) -> list[dict]: ...

    @abstractmethod
    def get_dynamic_list(
        self,
        settings: T,
        wildcard: str,
        refnr: str,
    ) -> list[dict]: ...