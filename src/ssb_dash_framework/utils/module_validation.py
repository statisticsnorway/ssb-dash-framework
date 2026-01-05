import logging
from typing import Any

logger = logging.getLogger(__name__)


def module_validator(module_class: Any) -> None:
    """This function validates a module class against certain criteria.

    Usage is optional, but ensures that the class has the required attributes and methods to function correctly within the framework.
    It also ensures that the class can use the mixins for implementing the module, see implementations.py to see the mixin classes.

    Args:
        module_class: The instantiated class to validate.

    Raises:
        AttributeError: If the class does not have the required attributes.

    Example:
        >>> from ssb_dash_framework.utils.module_validation import module_validator
        >>> class MyModule:
        ...     _id_number = 0
        ...     def __init__(self):
        ...         self.module_number = MyModule._id_number
        ...         self.module_name = self.__class__.__name__
        ...         MyModule._id_number += 1
        ...         self.module_layout = None
        ...         self.icon = None
        ...         self.label = None
        ...         self.module_callbacks = None
        ...         module_validator(self)
        ...     def layout(self):
        ...         pass
        ...     def module_callbacks(self):
        ...         pass
        >>> my_module = MyModule()

    Notes:
        - It is highly recommended to add this function in the `__init__` method of your module class.
        - This validation works best if used in combination with a test that makes sure the class can be instantiated.
    """
    if not hasattr(module_class, "_id_number"):
        raise AttributeError("Missing _id_number classvar")
    if not hasattr(module_class, "module_number"):
        raise AttributeError(
            f"Class {module_class} must have a 'module_number' attribute."
        )
    if not hasattr(module_class, "module_name"):
        raise AttributeError(
            f"Class {module_class} must have a 'module_name' attribute."
        )
    if not hasattr(module_class, "module_layout"):
        raise AttributeError(
            f"Class {module_class} must have a 'module_layout' attribute."
        )
    if not hasattr(module_class, "icon"):
        logger.warning(
            f"Class {module_class} does not have an 'icon' attribute. "
            "Icon is optional, but recommended for better user experience."
        )
    if not hasattr(module_class, "label"):
        raise AttributeError(f"Class {module_class} must have a 'label' attribute.")
    if not hasattr(module_class, "module_callbacks"):
        raise AttributeError(
            f"Class {module_class} must have a 'module_callbacks' method."
        )
    if not hasattr(module_class, "layout"):
        raise AttributeError(f"Class {module_class} must have a 'layout' method.")
