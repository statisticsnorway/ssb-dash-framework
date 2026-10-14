import logging
from dataclasses import dataclass
from enum import Enum

import pendulum
from pydantic import BaseModel
from pydantic import field_validator

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
