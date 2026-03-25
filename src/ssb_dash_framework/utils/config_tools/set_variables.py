""""""

from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from ...setup.variableselector import VariableSelectorOption


class TimeUnitType(Enum):
    YEAR = 1
    HALF_YEAR = 2
    QUARTER = 3
    MONTH = 4
    WEEK = 5
    DAY = 6


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
        raise TypeError(f"Invalid type for 'refnr_variable_name'. Expected type 'str'. Received '{type(refnr_variable_name)}'.")
    VariableSelectorOption(refnr_variable_name)
    REFNR = refnr_variable_name


TIME_UNITS: dict[str, TimeUnitType] | None = None


def get_time_units() -> dict[str, TimeUnitType]:
    global TIME_UNITS
    if not TIME_UNITS:
        raise RuntimeError("Time_units has not been defined through 'set_time_units()'.")
    return TIME_UNITS


def set_time_units(time_units: dict[str, TimeUnitType]) -> None:
    global TIME_UNITS

    if not isinstance(time_units, dict):
        raise TypeError("time_units must be a dict[str, TimeUnitType]")

    for key, value in time_units.items():
        if not isinstance(key, str):
            raise TypeError(f"Invalid key {key!r}: keys must be str")

        if not isinstance(value, TimeUnitType):
            raise TypeError(
                f"Invalid value for '{key}': {value!r} must be TimeUnitType"
            )
        VariableSelectorOption(key)

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
        raise TypeError(f"Invalid type for 'ident'. Expected type 'str'. Received '{type(ident)}'.")
    VariableSelectorOption(ident)
    IDENT = ident


SECONDARY_IDENTS: list[str] | None = None


def get_secondary_idents() -> list[str]:
    global SECONDARY_IDENTS
    if not SECONDARY_IDENTS:
        raise RuntimeError("secondary_idents has not been defined through 'set_secondary_idents()'.")
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
        raise RuntimeError("Groupingvariables has not been defined through 'set_groupingvariables()'.")
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
