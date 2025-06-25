from ..modules import BofInformation
from ..utils import TabImplementation


class BofInformationTab(TabImplementation, BofInformation):
    """A class to implement a bof information module as a tab."""

    def __init__(self, label=None, variableselector_foretak_name=None) -> None:
        """Initialize the BofInformationTab.

        This class is used to create a tab to put in the tab_list.
        """
        BofInformation.__init__(
            self,
            label=label,
            variableselector_foretak_name=variableselector_foretak_name,
        )
        TabImplementation.__init__(self)
