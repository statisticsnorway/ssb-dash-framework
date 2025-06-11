from ..modules import BofInformation
from ..utils import TabImplementation


class BofInformationTab(TabImplementation, BofInformation):
    """A class to implement a bof information module as a tab."""

    def __init__(self) -> None:
        """Initialize the BofInformationTab.

        This class is used to create a tab to put in the tab_list.
        """
        BofInformation.__init__(self)
        TabImplementation.__init__(self)
