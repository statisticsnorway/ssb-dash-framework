from abc import ABC
from abc import abstractmethod

from dash import html


class ModuleBaseClass(ABC):
    """Base class for SSB Dash Framework modules."""

    def __init__(self) -> None:
        if "_id_number" not in self.__class__.__dict__:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define its own class variable '_id_number'"
            )
        if not hasattr(self, "label"):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define its own 'label' attribute"
            )
        if not hasattr(self, "module_name"):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define its own 'module_name' attribute"
            )
        if not hasattr(self, "module_number"):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define its own 'module_number' attribute"
            )
        if not hasattr(self, "module_layout"):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define its own 'module_layout' attribute"
            )
        super().__init__()

    @abstractmethod
    def layout(self) -> html.Div:
        pass

    @abstractmethod
    def module_callbacks(self, app) -> None:
        """Define the callbacks for the module."""
        pass
