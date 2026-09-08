""""""

import logging

from typing import Any

from pydantic import BaseModel
from pydantic import Field

from .variableselector import VariableSelector
from .variableselector import VariableSelectorOption
from .time_unit import TimeUnit
from .time_unit import TimeUnitType

logger = logging.getLogger(__name__)


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

    time_units: TimeUnit | None = Field(
        default=None, description="Mapping of variable name to time unit type"
    )

    grouping_variables: list[str] | None = Field(
        default=None, description="Variables used for grouping operations"
    )

    def model_post_init(self, __context: Any) -> None:
        apply_config(self)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "VariableSelectorConfig":
        import yaml

        with open(yaml_path) as f:
            config = yaml.safe_load(f)
        for unit in config["time_units"]:
            if config["time_units"][unit] == "year":
                config["time_units"][unit] = TimeUnitType.YEAR
            elif config["time_units"][unit] == "half-year":
                config["time_units"][unit] = TimeUnitType.HALF_YEAR
            elif config["time_units"][unit] == "quarter":
                config["time_units"][unit] = TimeUnitType.QUARTER
            elif config["time_units"][unit] == "month":
                config["time_units"][unit] = TimeUnitType.MONTH
            elif config["time_units"][unit] == "week":
                config["time_units"][unit] = TimeUnitType.WEEK
            elif config["time_units"][unit] == "day":
                config["time_units"][unit] = TimeUnitType.DAY
            else:
                raise RuntimeError(
                    "The time unit you selected was invalid. Allowed values: year, half-year, quarter, month, week, day"
                )
        return cls(**config)

    @classmethod
    def from_dict(cls, config) -> "VariableSelectorConfig":
        for unit in config["time_units"]:
            if config["time_units"][unit] == "year":
                config["time_units"][unit] = TimeUnitType.YEAR
            elif config["time_units"][unit] == "half-year":
                config["time_units"][unit] = TimeUnitType.HALF_YEAR
            elif config["time_units"][unit] == "quarter":
                config["time_units"][unit] = TimeUnitType.QUARTER
            elif config["time_units"][unit] == "month":
                config["time_units"][unit] = TimeUnitType.MONTH
            elif config["time_units"][unit] == "week":
                config["time_units"][unit] = TimeUnitType.WEEK
            elif config["time_units"][unit] == "day":
                config["time_units"][unit] = TimeUnitType.DAY
            else:
                raise RuntimeError(
                    "The time unit you selected was invalid. Allowed values: year, half-year, quarter, month, week, day"
                )
        return cls(**config)

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
            # for var, unit_type in self.time_units.items():
            lines.append(f"    {self.time_units.name:<30} {self.time_units.frequency}")
        else:
            lines.append("  time_units:           (not set)")

        return "\n".join(lines)


def apply_config(config: VariableSelectorConfig) -> None:
    if config.time_units:
        VariableSelector._time_unit = config.time_units
        VariableSelectorOption(config.time_units.name)

    if config.ident:
        VariableSelector._ident = config.ident
        VariableSelectorOption(config.ident)

    if config.refnr:
        VariableSelector._refnr = config.refnr
        VariableSelectorOption(config.refnr)

    if config.secondary_idents:
        VariableSelector._secondary_ident = config.secondary_idents
        for var in config.secondary_idents:
            VariableSelectorOption(var)

    if config.grouping_variables:
        VariableSelector._grouping_variables = config.grouping_variables
        for var in config.grouping_variables:
            VariableSelectorOption(var)
