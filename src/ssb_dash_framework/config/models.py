import inspect
import os
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from ..utils.config_tools.set_variables import TimeUnitType
from ..utils.config_tools.set_variables import apply_config
from ..utils.implementations import TabImplementation
from ..utils.implementations import WindowImplementation


class RegisteredModule(BaseModel):
    type: str
    as_tab: str | None
    as_window: str | None
    kwargs: list[str]


_MODULE_REGISTRY: list[RegisteredModule] = list()


def get_module_registry():
    global _MODULE_REGISTRY
    return _MODULE_REGISTRY


def get_from_module_registry(module_name: str) -> RegisteredModule:
    """Gets a registered module from the registry."""
    global _MODULE_REGISTRY
    hits = [module for module in _MODULE_REGISTRY if module.type == module_name]
    if len(hits) < 1:
        for i in _MODULE_REGISTRY:
            print(i)
        raise ValueError(f"No module named '{module_name}' found.")
    if len(hits) > 1:
        raise ValueError(f"Several modules found for name '{module_name}': {hits}")
    return hits[0]


def register_module(as_tab: str | None = None, as_window: str | None = None):
    # TODO: consider gathering all modules to be registered to a list, and then registering after
    # running 'register_implementation_modules()' to prevent unnecessary manual registering.
    """Decorator for registering a module that does not use TabImplementation or WindowImplementation."""

    def decorator(module):
        registry = get_module_registry()
        if module.__name__ in [
            registered_module.type for registered_module in registry
        ]:
            raise ValueError(f"Module '{module.__name__}' is already registered")
        model_signature = inspect.signature(module)
        registry.append(
            RegisteredModule(
                type=module.__name__,
                as_tab=as_tab,
                as_window=as_window,
                kwargs=list(model_signature.parameters.keys()),
            )
        )
        return module

    return decorator


def register_implementation_modules():
    tabs = {
        base: cls
        for cls in TabImplementation.__subclasses__()
        for base in cls.__bases__
        if base is not TabImplementation
    }
    windows = {
        base: cls
        for cls in WindowImplementation.__subclasses__()
        for base in cls.__bases__
        if base is not WindowImplementation
    }
    modules = list(set(tabs) | set(windows))
    for module in modules:
        if module.__name__ in [
            registered_module.type for registered_module in get_module_registry()
        ]:
            raise ValueError(f"Module '{module.__name__}' is already registered")
        model_signature = inspect.signature(module)
        _MODULE_REGISTRY.append(
            RegisteredModule(
                type=module.__name__,
                as_tab=tabs[module].__name__ if module in tabs else None,
                as_window=windows[module].__name__ if module in windows else None,
                kwargs=list(model_signature.parameters.keys()),
            )
        )


def register_modules():
    register_implementation_modules()


class VariableSelectorConfig(BaseModel):  # TODO Add default templates?
    """Configuration for the variable selector."""

    refnr: str | None = Field(
        default=None,
        description="Column containing reference number or similar unique identifier for observation.",
    )
    ident: str | None = Field(default=None, description="Primary identifier column")
    secondary_idents: list[str] | None = Field(
        default=None, description="Additional identifier columns"
    )
    time_units: dict[str, TimeUnitType] | None = Field(
        default=None, description="Mapping of variable name to time unit type"
    )
    grouping_variables: list[str] | None = Field(
        default=None, description="Variables used for grouping operations"
    )

    def model_post_init(self, __context: Any) -> None:
        apply_config(self)

    def __str__(self) -> str:
        lines = [
            "VariableSelectorConfig",
            f"  refnr:                {self.refnr or '(not set)'}",
            f"  ident:                {self.ident or '(not set)'}",
            f"  secondary_idents:     {', '.join(self.secondary_idents) if self.secondary_idents else '(not set)'}",
            f"  grouping_variables:   {', '.join(self.grouping_variables) if self.grouping_variables else '(not set)'}",
        ]

        if self.time_units:
            lines.append("  time_units:")
            for var, unit_type in self.time_units.items():
                lines.append(f"    {var:<30} {unit_type}")
        else:
            lines.append("  time_units:           (not set)")

        return "\n".join(lines)


class AppSettings(BaseModel):
    """Maps 1-to-1 onto the arguments of app_setup()."""

    port: int
    service_prefix: str = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
    stylesheet: str = "darkly"
    enable_logging: bool = True
    logging_level: Literal["debug", "info", "warning", "error", "critical"] = "info"
    log_to_file: bool = False
    variableselector: VariableSelectorConfig

    @field_validator("port")
    @classmethod
    def port_in_range(cls, v: int) -> int:
        if not (1024 <= v <= 65535):
            raise ValueError(f"port must be between 1024 and 65535, got {v}")
        return v

    def __str__(self) -> str:
        lines = [
            "AppSettings",
            f"  port:               {self.port}",
            f"  service_prefix:     {self.service_prefix}",
            f"  stylesheet:         {self.stylesheet}",
            f"  enable_logging:     {self.enable_logging}",
            f"  logging_level:      {self.logging_level}",
            f"  log_to_file:        {self.log_to_file}",
            "  variableselector:",
        ]

        vs_str = str(self.variableselector).splitlines()
        lines.extend(f"    {line}" for line in vs_str)

        return "\n".join(lines)


class ModuleConfig(BaseModel):
    """Represents one module entry in the YAML.

    The ``type`` field must match the class name exactly (e.g. ``FreeSearch``).
    All other keys in the YAML block become keyword arguments passed to the
    class constructor.

    Example YAML::

        - type: FreeSearch
          conn: null

        - type: HbMethod
          label: "HB Method"
          some_param: 42
    """

    model_config = {"extra": "allow"}

    type: str

    @model_validator(mode="before")
    @classmethod
    def _separate_type_from_kwargs(cls, data: Any) -> Any:
        """No-op validator — just ensures 'type' is present."""
        if isinstance(data, dict) and "type" not in data:
            raise ValueError("Each module entry must have a 'type' key.")
        return data

    @model_validator(mode="after")
    def _validate_kwargs_against_registry(self) -> "ModuleConfig":
        registered = get_from_module_registry(self.type)
        invalid = set(self.extra_kwargs) - set(registered.kwargs)
        if invalid:
            raise ValueError(
                f"Module {self.type!r} received unexpected kwargs: {invalid}. "
                f"Valid kwargs are: {registered.kwargs}"
            )
        return self

    @property
    def extra_kwargs(self) -> dict[str, Any]:
        """Return all fields that are NOT 'type', to be forwarded as **kwargs."""
        return self.model_extra or {}

    def __str__(self) -> str:
        lines = [self.type]

        for key, value in self.extra_kwargs.items():
            lines.append(f"    {key}={value!r}")

        return "\n".join(lines)


class AppModules(BaseModel):
    """Describes which modules appear as tabs and which as sidebar windows.

    ``tabs``    → passed as ``tab_list``    to main_layout()
    ``windows`` → passed as ``window_list`` to main_layout()
    """

    dataeditor_components: list[ModuleConfig] = []
    tabs: list[ModuleConfig] = []
    windows: list[ModuleConfig] = []

    def __str__(self) -> str:
        lines = [
            "AppModules",
            f"  tabs ({len(self.tabs)}):",
        ]
        if self.tabs:
            for module in self.tabs:
                module_lines = str(module).splitlines()

                lines.append(f"    - {module_lines[0]}")

                for line in module_lines[1:]:
                    lines.append(f"      {line}")
        else:
            lines.append("    (none)")
        lines.append(f"  windows ({len(self.windows)}):")
        if self.windows:
            for module in self.windows:
                module_lines = str(module).splitlines()

                lines.append(f"    - {module_lines[0]}")

                for line in module_lines[1:]:
                    lines.append(f"      {line}")
        else:
            lines.append("    (none)")
        return "\n".join(lines)


class AppConfig(BaseModel):
    """Root model — the entire YAML file maps onto this."""

    app_settings: AppSettings
    modules: AppModules = AppModules()

    def __str__(self) -> str:
        lines = [
            "AppConfig",
            "",
            str(self.app_settings),
            "",
            str(self.modules),
        ]

        return "\n".join(lines)
