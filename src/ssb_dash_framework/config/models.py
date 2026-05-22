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

    # @classmethod
    # def from_yaml(cls, yaml_path: str) -> "VariableSelectorConfig":
    #     import yaml

    #     with open(yaml_path) as f:
    #         config = yaml.safe_load(f)
    #     for unit in config["time_units"]:
    #         if config["time_units"][unit] == "year":
    #             config["time_units"][unit] = TimeUnitType.YEAR
    #     return cls(**config)

    # @classmethod
    # def from_dict(cls, config) -> "VariableSelectorConfig":
    #     for unit in config["time_units"]:
    #         if config["time_units"][unit] == "year":
    #             config["time_units"][unit] = TimeUnitType.YEAR
    #     return cls(**config)

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
    service_prefix: str | None = None
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


class AppModules(BaseModel):
    """Describes which modules appear as tabs and which as sidebar windows.

    ``tabs``    → passed as ``tab_list``    to main_layout()
    ``windows`` → passed as ``window_list`` to main_layout()
    """

    tabs: list[ModuleConfig] = []
    windows: list[ModuleConfig] = []


class AppConfig(BaseModel):
    """Root model — the entire YAML file maps onto this."""

    app_settings: AppSettings
    modules: AppModules = AppModules()
