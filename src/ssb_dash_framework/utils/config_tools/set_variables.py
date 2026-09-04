""""""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pendulum
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from ...setup.variableselector import VariableSelectorOption

logger = logging.getLogger(__name__)


class TimeUnitType(Enum):
    YEAR = 1
    HALF_YEAR = 2
    QUARTER = 3
    MONTH = 4
    WEEK = 5
    DAY = 6

    def to_fmt(self) -> str:
        match self:
            case TimeUnitType.DAY:
                return "YYYY-MM-DD"
            case TimeUnitType.WEEK:
                return "YYYY-[W]WW"
            case TimeUnitType.MONTH:
                return "YYYY-MM"
            case TimeUnitType.QUARTER:
                return "YYYY-[Q]M"
            case TimeUnitType.HALF_YEAR:
                return "YYYY-M"
            case TimeUnitType.YEAR:
                return "YYYY"


class TimeUnit(BaseModel):
    name: str
    frequency: TimeUnitType

    @field_validator("frequency", mode="before")
    @classmethod
    def parse_frequency(cls, value: str | TimeUnitType) -> TimeUnitType:
        print("TEST")
        if isinstance(value, TimeUnitType):
            return value

        try:
            return TimeUnitType[value.upper().replace("-", "_")]
        except KeyError:
            raise ValueError(f"Invalid time unit frequency: {value!r}")

    @staticmethod
    def parse(timeunit: "TimeUnit", period: str):
        """Utility method for turning callback information into a SelectedTimeUnit for easier handling."""
        match timeunit.frequency:
            case TimeUnitType.HALF_YEAR:
                year, year_half = period.split("-")
                if year_half == "1":
                    month = 1
                elif year_half == "2":
                    month = 7
                else:
                    raise RuntimeError(
                        f"Half year was selected as period. Format should be [YYYY-1|2], but recieved: {period}"
                    )
                dt = pendulum.datetime(int(year), month=month, day=1)

            case TimeUnitType.QUARTER:
                year, quarter = period.split("-")
                if quarter == "Q1":
                    month = 1
                elif quarter == "Q2":
                    month = 4
                elif quarter == "Q3":
                    month = 7
                elif quarter == "Q4":
                    month = 10
                else:
                    raise RuntimeError(
                        f"Quarter was selected as period. Format should be [YYYY-Q1|Q2|Q3|Q4], but recieved: {period}"
                    )
                dt = pendulum.datetime(int(year), month=month, day=1)
            case _:
                dt = pendulum.from_format(period, timeunit.frequency.to_fmt())

        return SelectedTimeUnit(timeunit=timeunit, dt=dt)


@dataclass
class SelectedTimeUnit:
    """A class for use inside callbacks where the period is parsed and with some utility methods for iterations"""

    timeunit: TimeUnit
    dt: pendulum.DateTime

    @staticmethod
    def _frequency_to_args(frequency: TimeUnitType, num_periods: int):
        match frequency:
            case TimeUnitType.DAY:
                return {"days": num_periods}
            case TimeUnitType.WEEK:
                return {"weeks": num_periods}
            case TimeUnitType.MONTH:
                return {"months": num_periods}
            case TimeUnitType.QUARTER:
                return {"months": 3 * num_periods}
            case TimeUnitType.HALF_YEAR:
                return {"months": 6 * num_periods}
            case TimeUnitType.YEAR:
                return {"years": num_periods}

    def add(self, num_periods: int) -> "SelectedTimeUnit":
        arg = self._frequency_to_args(self.timeunit.frequency, num_periods)
        new_dt = self.dt.add(**arg)
        return SelectedTimeUnit(timeunit=self.timeunit, dt=new_dt)

    def subtract(self, num_periods: int) -> "SelectedTimeUnit":
        arg = self._frequency_to_args(self.timeunit.frequency, num_periods)
        new_dt = self.dt.subtract(**arg)
        return SelectedTimeUnit(timeunit=self.timeunit, dt=new_dt)

    def to_str(self) -> str:
        match self.timeunit.frequency:
            case TimeUnitType.DAY:
                return self.dt.format("YYYY-MM-DD")
            case TimeUnitType.WEEK:
                return self.dt.format("YYYY-[W]WW")
            case TimeUnitType.MONTH:
                return self.dt.format("YYYY-MM")
            case TimeUnitType.QUARTER:
                if self.dt.month == 1:
                    return self.dt.format("YYYY-Q1")
                if self.dt.month == 4:
                    return self.dt.format("YYYY-Q2")
                if self.dt.month == 7:
                    return self.dt.format("YYYY-Q3")
                if self.dt.month == 10:
                    return self.dt.format("YYYY-Q4")
                else:
                    raise RuntimeError(
                        f"Period was set as quarter, but recieved a datetime that was incompatible: {self.dt}"
                    )
            case TimeUnitType.HALF_YEAR:
                if self.dt.month == 1:
                    return self.dt.format("YYYY-1")
                if self.dt.month == 7:
                    return self.dt.format("YYYY-2")
                else:
                    raise RuntimeError(
                        f"Period was set as half-year, but recieved a datetime that was incompatible: {self.dt}"
                    )
            case TimeUnitType.YEAR:
                return self.dt.format("YYYY")


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
        return cls(**config)

    @classmethod
    def from_dict(cls, config) -> "VariableSelectorConfig":
        for unit in config["time_units"]:
            if config["time_units"][unit] == "year":
                config["time_units"][unit] = TimeUnitType.YEAR
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
    if config.refnr:
        set_refnr(config.refnr)

    if config.ident:
        set_ident(config.ident)

    if config.secondary_idents:
        set_secondary_idents(config.secondary_idents)

    if config.time_units:
        set_time_units(config.time_units)

    if config.grouping_variables:
        set_groupingvariables(config.grouping_variables)


REFNR: str | None = None


def get_refnr() -> str:
    global REFNR
    if not REFNR:
        raise RuntimeError("Refnr has not been defined through 'set_refnr()'.")
    return REFNR


def set_refnr(refnr_variable_name: str) -> None:
    global REFNR
    if not isinstance(refnr_variable_name, str):
        raise TypeError(
            f"Invalid type for 'refnr_variable_name'. Expected type 'str'. Received '{type(refnr_variable_name)}'."
        )
    VariableSelectorOption(refnr_variable_name)
    REFNR = refnr_variable_name


TIME_UNITS: TimeUnit | None = None


def get_time_units() -> TimeUnit:
    global TIME_UNITS
    if not TIME_UNITS:
        raise RuntimeError(
            "Time_units has not been defined through 'set_time_units()'."
        )
    return TIME_UNITS


def set_time_units(time_units: TimeUnit) -> None:
    global TIME_UNITS

    if not isinstance(time_units, TimeUnit):
        raise TypeError("time_units must be a TimeUnit")

    VariableSelectorOption(time_units.name)

    TIME_UNITS = time_units


IDENT: str | None = None


def get_ident() -> str:
    global IDENT
    if not IDENT:
        raise RuntimeError("Ident has not been defined through 'set_ident()'.")
    return IDENT


def set_ident(ident: str) -> None:
    global IDENT
    if not isinstance(ident, str):
        raise TypeError(
            f"Invalid type for 'ident'. Expected type 'str'. Received '{type(ident)}'."
        )
    VariableSelectorOption(ident)
    IDENT = ident


SECONDARY_IDENTS: list[str] | None = None


def get_secondary_idents() -> list[str]:
    global SECONDARY_IDENTS
    if not SECONDARY_IDENTS:
        raise RuntimeError(
            "secondary_idents has not been defined through 'set_secondary_idents()'."
        )
    return SECONDARY_IDENTS


def set_secondary_idents(secondary_idents: list[str]) -> None:
    global SECONDARY_IDENTS
    for secondary_ident_name in secondary_idents:
        if not isinstance(secondary_ident_name, str):
            raise TypeError(
                f"Invalid type for '{secondary_ident_name}'. Expected 'str', received '{type(secondary_ident_name)}'"
            )
        VariableSelectorOption(secondary_ident_name)
    SECONDARY_IDENTS = secondary_idents


GROUPINGVARIABLES: list[str] | None = None


def get_groupingvariables() -> list[str]:
    global GROUPINGVARIABLES
    if not GROUPINGVARIABLES:
        raise RuntimeError(
            "Groupingvariables has not been defined through 'set_groupingvariables()'."
        )
    return GROUPINGVARIABLES


def set_groupingvariables(groupingvariables: list[str]) -> None:
    global GROUPINGVARIABLES
    for group in groupingvariables:
        if not isinstance(group, str):
            raise TypeError(
                f"Invalid type for '{group}'. Expected 'str', received '{type(group)}'"
            )
        VariableSelectorOption(group)
    GROUPINGVARIABLES = groupingvariables
