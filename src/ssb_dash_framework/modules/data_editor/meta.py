from abc import abstractmethod

from dash import html

from .utils import EditorSettings

from .modules.inforow.meta import InforowMeta
from .modules.helper_buttons.meta import HelperButtonMeta
from .modules.microlayout.meta import MicrolayoutMeta

from ...utils.base_classes import YamlLoadable

SettingsType = EditorSettings


class FetcherMeta(
    YamlLoadable,
    # SidebarMeta[SettingsType],
    InforowMeta[SettingsType],
    HelperButtonMeta,
    MicrolayoutMeta[SettingsType],
):
    """Unified data retrieval interface combining all data editor metadata capabilities.

    This interface consolidates fetching methods for inforows, sidebars, helper buttons,
    and microlayout forms to communicate with backend databases.
    """
    ...


class ContextABC(YamlLoadable):
    """Base class for defining a module operating within a specific database and layout context.

    Attributes:
        fetcher (FetcherMeta): The data fetching handler.
        settings (EditorSettings): The configuration settings for the editor.
        instance_id (str): A unique ID to separate distinct instances of modules.
    """

    fetcher: FetcherMeta
    settings: EditorSettings
    instance_id: str

    def set_settings(
        self, fetcher: FetcherMeta, settings: EditorSettings, instance_id: str
    ):
        """Configures the context variables for the module.

        Args:
            fetcher: An implementation of the database query interface.
            settings: Active editor configuration settings.
            instance_id: A unique identifier for this module instance.
        """
        self.fetcher = fetcher
        self.settings = settings
        self.instance_id = instance_id


class ModuleABC(ContextABC):
    """Base class for defining a layout-rendering helper sidebar or editor component."""

    @abstractmethod
    def layout(self) -> html.Div:
        """Returns the layout of the module."""
        ...

    @abstractmethod
    def module_callbacks(self) -> None:
        """Registers callbacks for the module."""
        ...
