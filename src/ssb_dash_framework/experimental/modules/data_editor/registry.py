from typing import Any
from typing import ClassVar


class DataEditorRegistry:
    """Helper class to keep track of what has been added to the DataEditor."""

    info_fields: ClassVar[list[Any]] = []
    helper_modules: ClassVar[list[Any]] = []
    sidebar_modules: ClassVar[list[Any]] = []
    main_views: ClassVar[dict[Any, Any]] = dict()
    _table_form_covered: ClassVar[list[tuple[str, str]]] = []
