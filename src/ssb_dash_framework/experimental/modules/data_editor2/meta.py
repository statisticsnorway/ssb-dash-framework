from abc import ABC, abstractmethod
from typing import Any
import pandas as pd
from dash import html
from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_custom import (
    CallbackSettings,
)
from .modules.info_row_model import (
    InfoRowField,
)
from .modules.microlayout.microlayout_components.editable_field_model import (
    FieldCallbackContainer,
)
from .utils import EditorSettings, RefnrStatus


class FetcherMeta(ABC):
    @abstractmethod
    def get_field(
        self,
        settings: CallbackSettings,
        container: FieldCallbackContainer,
        inputs: list[Any] | dict[Any, Any],
    ) -> Any: ...

    @abstractmethod
    def get_form_status(self, refnr: str) -> RefnrStatus | None: ...

    @abstractmethod
    def get_refnrs_by_period_ident(
        self, settings: EditorSettings, ident: str, period: str
    ) -> pd.DataFrame | None: ...

    @abstractmethod
    def get_comment(self, refnr: str) -> str | None: ...

    @abstractmethod
    def get_history(self, refnr: str) -> pd.DataFrame: ...

    @abstractmethod
    def get_info_row_fields(
        self,
        settings: EditorSettings,
        ident: str,
        period: str,
        fields: list[InfoRowField],
    ) -> dict[str, str | int | bool | float | None]: ...

    @abstractmethod
    def get_timeseries(
        self,
        variable: str,
        refnr: str,
        ident: str,
        periods: list[str],
    ) -> list[dict]: ...


class ContextABC(ABC):
    """Base class for defining a contexted module."""

    fetcher: FetcherMeta
    settings: EditorSettings

    def set_settings(self, fetcher: FetcherMeta, settings: EditorSettings):
        self.fetcher = fetcher
        self.settings = settings


class ModuleABC(ContextABC):
    """Base class for defining a helper sidebar component."""

    @abstractmethod
    def _create_layout(self) -> html.Div:
        """Creates the layout for the module."""
        pass

    def layout(self) -> html.Div:
        """Returns the layout of the module."""
        return self._create_layout()

    @abstractmethod
    def module_callbacks(self) -> None:
        """Registers callbacks for the module."""
        pass
