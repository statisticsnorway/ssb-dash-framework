from logging import getLogger
from typing import Any
from dash import State, Input, Output, callback
from dash.exceptions import PreventUpdate
from .....setup.variableselector import VariableSelector
from .....utils.config_tools.set_variables import get_ident
from .....utils.config_tools.set_variables import get_time_units
from .....utils.core_query_functions import create_filter_dict
from ..meta import ModuleABC
from .info_row_model import InfoRowField
import dash_bootstrap_components as dbc

logger = getLogger(__name__)


class DataEditorInfoRow(ModuleABC):
    """Creates a row of cards at top of DataEditor showing key variables for selected form."""

    _id_number = 0

    def __init__(
        self, variables: dict[str, Any] | list[InfoRowField]
    ) -> None:  # TODO make pydantic class for an info field.
        """Initializes the info row for the DataEditor.

        Args:
            variables: A list of InfoRowField objects or a dict where the key is the label for the variable.
                In a dict the values must be {source: "sourcetable", variable_name: "variable name in table"}

        Raises:
            TypeError: If 'variables' is not list of InfoRowField objects or a compatible dict.

        """
        self.module_number = DataEditorInfoRow._id_number
        self.module_name = self.__class__.__name__
        DataEditorInfoRow._id_number += 1

        if isinstance(variables, dict):
            _vars = []
            for var in variables:
                _vars.append(
                    InfoRowField(
                        name=var,
                        source=variables[var]["source"],
                        source_variable_name=variables[var]["variable_name"],
                    )
                )
            self.info_variables = _vars
        elif isinstance(variables, list) and all(
            isinstance(v, InfoRowField) for v in variables
        ):
            self.info_variables = variables
        else:
            raise TypeError(
                "Argument 'variables' must be either list of InfoRowField or a dictionary that is convertable to a list of InfoRowField."
            )
        self.module_callbacks()

    def _create_layout(self) -> dbc.Row: # pyright: ignore
        info_fields = []
        for info_var in self.info_variables:
            info_fields.append(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            id=f"info-var-label-{info_var.name}", children=info_var.name
                        ), # pyright: ignore
                        dbc.CardBody(id=f"info-var-field-{info_var.name}"), # pyright: ignore
                    ]
                ) # pyright: ignore
            )

        return dbc.Row(
            dbc.CardGroup(info_fields), className=f"{self.module_name}-info-row"
        ) # pyright: ignore

    def layout(self) -> dbc.Row: # pyright: ignore
        """Returns the module layout."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Registers callbacks for the module."""
        variableselector = VariableSelector(
            selected_inputs=[],
            selected_states=[
                x.source_variable_name
                for x in self.info_variables
                if x.source == "variableselector"
            ],
        )

        @callback(
            output={
                info_var.name: Output(f"info-var-field-{info_var.name}", "children")
                for info_var in self.info_variables
            },
            inputs={
                "ident": variableselector.get_input(get_ident()),
                "period": variableselector.get_input(get_time_units().name),
                "states": {item.component_id: item for item in variableselector.get_all_states()}
            },
        )
        def get_data_for_info_row_fields(
            ident: str, period: str, states: dict[str, dict]
        ) -> dict[str, str | int | float | bool | None]:
            logger.debug(f"ident: {ident}\nperiod: {period}\nstates: {states}")
            if not ident or not period or not states:
                raise PreventUpdate
            info_values = {}
            vars_to_collect = []
            for item in self.info_variables:
                if item.source == "variableselector":
                    value = states[f"var-{item.source_variable_name}"]
                    info_values[item.name] = value
                else:
                    vars_to_collect.append(item)

            field_data = self.fetcher.get_info_row_fields(self.settings, ident, period, vars_to_collect)
            info_values.update(field_data)

            logger.debug(f"info_values: {info_values}")
            return info_values