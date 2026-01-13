from typing import ClassVar


class AltinnEditorStateTracker:
    """Helper class for keeping track of information."""

    valid_altinnedit_options: ClassVar[set[str]] = set()

    @classmethod
    def register_option(cls, option: str) -> None:
        """Adds option to list of valid options."""
        cls.valid_altinnedit_options.add(option)

    @classmethod
    def get_options(cls, option: str) -> set[str]:
        """Retrieves list of valid options."""
        return set(cls.valid_altinnedit_options)
