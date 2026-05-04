from typing import Any
import pendulum

from pydantic import Field
from pydantic import BaseModel
from pydantic_extra_types.pendulum_dt import DateTime

from ....utils.config_tools.set_variables import TimeUnitType


class Period(BaseModel):
    year: int
    half_year: int = Field(default=1)
    month: int = Field(default=1)
    week: int = Field(default=1)
    day: int = Field(default=1)
    quarter: int = Field(default=1)

    def to_dt(self):
        
        return pendulum.datetime(self.year, self.month, self.day)


class PeriodModel(BaseModel):
    start: DateTime
    end: DateTime
    frequency: TimeUnitType

    @staticmethod
    def from_start(start: Period, frequency: TimeUnitType):
        end = start.to_dt()
        match frequency:
            case TimeUnitType.DAY:
                end = end.add(days=1)
            case TimeUnitType.WEEK:
                end = end.add(weeks=1)
            case TimeUnitType.MONTH:
                end = end.add(months=1)
            case TimeUnitType.QUARTER:
                end = end.add(months=4)
            case TimeUnitType.HALF_YEAR:
                end = end.add(months=6)
            case TimeUnitType.YEAR:
                end = end.add(years=1)

        return PeriodModel(start=start.to_dt(), end=end, frequency=frequency)

    @staticmethod
    def from_dict(time: dict[TimeUnitType, Any]):
        # if TimeUnitType.YEAR not in time:
        #       raise PreventUpdate

        start_period = Period(
            year=time[TimeUnitType.YEAR],
            half_year=time.get(TimeUnitType.HALF_YEAR, 1),
            month=time.get(TimeUnitType.MONTH, 1),
            week=time.get(TimeUnitType.WEEK, 1),
            day=time.get(TimeUnitType.DAY, 1),
            quarter=time.get(TimeUnitType.QUARTER, 1),
        )
        highest_frequency = max(time, key=lambda x: x.value)
        period = PeriodModel.from_start(start_period, highest_frequency)
        return period

    def iter(self, periods: int):
        return PeriodIterator(periods, self)


class PeriodIterator:
    def __init__(self, periods: int, model: PeriodModel):
        self.current = 0
        self.start = model
        self.end = periods

    def __iter__(self):
        return self  # The iterator object itself

    def __next__(self) -> PeriodModel:
        if self.current >= self.end:
            raise StopIteration  # End of iteration
        value = self.start

        match self.start.frequency:
            case TimeUnitType.DAY:
                value = PeriodModel(
                    start=self.start.start.add(days=self.current),
                    end=self.start.end.add(days=self.current),
                    frequency=TimeUnitType.DAY,
                )
            case TimeUnitType.WEEK:
                value = PeriodModel(
                    start=self.start.start.add(weeks=self.current),
                    end=self.start.end.add(weeks=self.current),
                    frequency=TimeUnitType.WEEK,
                )
            case TimeUnitType.MONTH:
                value = PeriodModel(
                    start=self.start.start.add(months=self.current),
                    end=self.start.end.add(months=self.current),
                    frequency=TimeUnitType.MONTH,
                )
            case TimeUnitType.QUARTER:
                value = PeriodModel(
                    start=self.start.start.add(months=self.current * 4),
                    end=self.start.end.add(months=self.current * 4),
                    frequency=TimeUnitType.QUARTER,
                )
            case TimeUnitType.HALF_YEAR:
                value = PeriodModel(
                    start=self.start.start.add(months=self.current * 6),
                    end=self.start.end.add(months=self.current * 6),
                    frequency=TimeUnitType.HALF_YEAR,
                )
            case TimeUnitType.YEAR:
                value = PeriodModel(
                    start=self.start.start.add(years=self.current),
                    end=self.start.end.add(years=self.current),
                    frequency=TimeUnitType.YEAR,
                )
        self.current += 1
        return value
