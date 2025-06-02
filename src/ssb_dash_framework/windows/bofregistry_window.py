from ..modules import BofInformation
from ..utils import WindowImplementation


class BofInformationWindow(WindowImplementation, BofInformation):
    """A class to implement a bof information module as a window."""

    def __init__(self) -> None:
        """Initialize the BofInformationTab.

        This class is used to create a tab to put in the tab_list.
        """
        BofInformation.__init__(self)
        WindowImplementation.__init__(self)
