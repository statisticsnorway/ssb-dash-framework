from typing import Any
from typing import ClassVar


class DataEditorRegistry:
    """Helper class to keep track of what has been added to the DataEditor.

    Note:
        This class can be printed to check currently registered modules and covered table-form pairs.
    """

    # Should get more specific type hints maybe?
    info_fields: ClassVar[list[Any]] = []
    helper_modules: ClassVar[list[Any]] = []
    sidebar_modules: ClassVar[list[Any]] = []
    main_views: ClassVar[dict[Any, Any]] = dict()
    _table_form_covered: ClassVar[list[tuple[str, str]]] = []

    def __str__(self) -> str:
        """Creates a string representation giving information about currently registered modules and table-form pairs."""
        lines = ["info_fields:"]
        for field in self.info_fields:
            lines.append(f"{field}")
        lines.append("Helper modules:")
        for helper in self.helper_modules:
            lines.append(f"{helper}")
        for sidebar_module in self.sidebar_modules:
            lines.append(f"{sidebar_module}")
        for view in self.main_views:
            lines.append(f"{view}")
        lines.append("Table - Form pairs covered:")
        for pair in self._table_form_covered:
            lines.append(f"{pair}")
        return "\n".join(lines)
