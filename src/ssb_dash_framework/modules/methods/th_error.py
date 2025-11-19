from collections.abc import Callable
from typing import Any
from typing import ClassVar

from vaskify import Detect


class ThError:
    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = ["ident"]

    def __init__(
        self,
        get_data_func: Callable[..., Any],
        time_units: list[str],
        value_var: str,
    ) -> None:
        self.module_number = ThError._id_number
        self.module_name = self.__class__.__name__
        ThError._id_number += 1

        self.icon = "🥼"
        self.label = "HB metoden"
        self.variable: str | None = None
        self.value_var = value_var

        self.time_units = time_units
        self.get_data_func = get_data_func

    def run_therror(self, *args):
        data = self.get_data_func(args)
        detect = Detect(data=t.to_pandas(), id_nr="ident")

        results = detect.thousand_error(
            "verdi", time_var="aar", output_format="outliers"
        )
