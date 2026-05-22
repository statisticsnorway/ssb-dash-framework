import os
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from ..utils.config_tools.set_variables import TimeUnitType
from ..utils.config_tools.set_variables import apply_config


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

    The ``type`` field must match the class name exactly (e.g. ``FreeSearchTab``).
    All other keys in the YAML block become keyword arguments passed to the
    class constructor.

    Example YAML::

        - type: FreeSearchTab
          conn: null

        - type: HbMethodTab
          label: "HB Method"
          some_param: 42
    """

    model_config = {"extra": "allow"}  # allow arbitrary kwargs

    type: str
    # Everything else is captured as extra fields and exposed via `extra_kwargs`.

    @model_validator(mode="before")
    @classmethod
    def _separate_type_from_kwargs(cls, data: Any) -> Any:
        """No-op validator — just ensures 'type' is present."""
        if isinstance(data, dict) and "type" not in data:
            raise ValueError("Each module entry must have a 'type' key.")
        return data

    @property
    def extra_kwargs(self) -> dict[str, Any]:
        """Return all fields that are NOT 'type', to be forwarded as **kwargs."""
        return {k: v for k, v in self.model_dump().items() if k != "type"}

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
