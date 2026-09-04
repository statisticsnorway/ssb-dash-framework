from abc import ABC
from abc import abstractmethod

from dash import html

from .utils import EditorSettings

from .modules.sidebar.meta import SidebarMeta
from .modules.inforow.meta import InforowMeta
from .modules.helper_buttons.meta import HelperButtonMeta
from .modules.microlayout.meta import MicrolayoutMeta

SettingsType = EditorSettings

class FetcherMeta(
    SidebarMeta[SettingsType],
    InforowMeta[SettingsType],
    HelperButtonMeta,
    MicrolayoutMeta[SettingsType],
):
    ...


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
