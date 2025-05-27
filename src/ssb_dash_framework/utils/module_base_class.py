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
        super().__init__()

    @property
    @abstractmethod
    def label(self) -> str:
        """"""
        pass

    @property
    @abstractmethod
    def module_name(self) -> str:
        """"""
        pass

    @property
    @abstractmethod
    def module_number(self) -> str:
        """"""
        pass

    @abstractmethod
    def layout(self) -> html.Div:
        pass
