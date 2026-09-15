from abc import abstractmethod, ABC

import pandas as pd


class HelperButtonMeta(ABC):
    @abstractmethod
    def get_history(self, refnr: str, insert_toggle: bool | None = None) -> pd.DataFrame: ...
