def module_validator(module_class):
    """"""
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
    if not hasattr(module_class, "label"):
        raise AttributeError(f"Class {module_class} must have a 'label' attribute.")
    if not hasattr(module_class, "module_callbacks"):
        raise AttributeError(
            f"Class {module_class} must have a 'module_callbacks' method."
        )
    if not hasattr(module_class, "layout"):
        raise AttributeError(f"Class {module_class} must have a 'layout' method.")
