"""This serves as an example of a module."""

from abc import abstractmethod, ABC
#from ..utils.

class HelloModuleMetaDataHandler(ABC):


    abstractmethod
    def get_message():
        pass

    abstractmethod
    def update_message():
        pass


class HelloModule(ModuleBase):
    ...