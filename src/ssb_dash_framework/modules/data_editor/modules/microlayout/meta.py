from abc import abstractmethod
from typing import Any

from .microlayout_components.editable_field_model import FieldCallbackContainer
from ..sidebar.meta import SidebarMeta

class MicrolayoutMeta[T](SidebarMeta):
    @abstractmethod
    def get_field(
        self,
        settings: T,
        container: FieldCallbackContainer,
        inputs: list[Any] | dict[Any, Any],
    ) -> Any: ...

    @abstractmethod
    def update_field_value(
        self,
        refnr: str,
        ident: str,
        value: Any,
        old_value: Any,
        settings: T,
        container: FieldCallbackContainer,
        inputs: list[Any] | dict[Any, Any],
        editing_code: str | None
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