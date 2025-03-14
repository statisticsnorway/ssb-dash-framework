import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html

from ..utils.alert_handler import create_alert

logger = logging.getLogger(__name__)


class VariableSelector:
    """Class containing options for shared states between modules in the framework.

    Notes:
        - Each module should have its own instance of the VariableSelector in its __init__ function.
    """

    _variableselectoroptions: list["VariableSelectorOption"] = []

    def __init__(
        self,
        selected_inputs: list[str],
        selected_states: list[str],
        default_values: dict[str, str | int | float] | None = None,
    ) -> None:
        """Initializes the VariableSelector class.

        Args:
            selected_inputs (List[str]): List of selected input variable names. Will trigger callbacks.
            selected_states (List[str]): List of selected state variable names. Will not trigger callbacks.
            default_values (Optional[Dict[str, Union[str, int, float]]], optional):
                Default values for variables. Defaults to None.

        Examples:
            >>> VariableSelector(selected_inputs = ["foretak"], selected_states = ["aar"])
            >>> VariableSelector(selected_inputs = ["foretak"], selected_states = ["aar"], default_values = {"aar": 2024})
        """
        self.options = [option.title for option in self._variableselectoroptions]
        self.inputs = selected_inputs
        self.states = selected_states
        self.selected_variables = [*selected_inputs, *selected_states]
        self.default_values = default_values

        self.is_valid()
        if default_values:
            self.default_values_is_valid()

    def is_valid(self) -> None:
        valid_states_inputs = [
            option.title for option in VariableSelector._variableselectoroptions
        ]
        for _option in self._variableselectoroptions:
            if not isinstance(_option, VariableSelectorOption):
                raise TypeError(
                    f"Invalid type. Should only contain values of type VariableSelectorOption. Received type: {type(_option)}: {_option}"
                )

        for _input in self.inputs:
            if _input not in valid_states_inputs:
                raise ValueError(
                    f"Invalid value for selected_inputs. Received {_input}. Expected one of {valid_states_inputs}"
                )
        for _state in self.states:
            if _state not in valid_states_inputs:
                raise ValueError(
                    f"Invalid value for selected_states. Received {_state}. Expected one of {valid_states_inputs}"
                )

    def default_values_is_valid(self) -> None:
        """Validates the default values dictionary."""
        if not isinstance(self.default_values, dict):
            raise TypeError(
                f"Expected default_values to be dict, received {type(self.default_values)}"
            )
        valid_states_inputs = [
            option.title for option in VariableSelector._variableselectoroptions
        ]
        for key in self.default_values:
            if key not in valid_states_inputs:
                raise KeyError(
                    f"Invalid key for default_values. Received {key}. Expected one of {valid_states_inputs}"
                )
            if self.get_option(key).type == "text":
                if not isinstance(self.default_values[key], str):
                    raise TypeError(
                        f"Invalid type for {key} in default_value. Received type {type(self.default_values[key])} Expected string."
                    )
            if self.get_option(key).type == "number":
                if not isinstance(self.default_values[key], (int, float)):
                    raise TypeError(
                        f"Invalid type for {key} in default_value. Received type {type(self.default_values[key])} Expected int or float."
                    )

    def get_option(self, variable_name: str) -> "VariableSelectorOption":
        """Retrieves a VariableSelectorOption by variable name."""
        for option in self._variableselectoroptions:
            if option.title == variable_name:
                return option
        raise ValueError(
            f"ValueError: {variable_name} not in list of options, expected one of {self.selected_variables}\nIf you need to add {variable_name} to the available options, refer to the VariableSelectorOption docstring."
        )

    def get_inputs(self) -> list[Input]:
        """Retrieves a list of Dash Input objects for selected inputs."""
        return [
            Input(option.id, "value")
            for option in self._variableselectoroptions
            if option.title in self.inputs
        ]

    def get_states(self) -> list[State]:
        """Retrieves a list of Dash State objects for selected states."""
        return [
            State(option.id, "value")
            for option in self._variableselectoroptions
            if option.title in self.states
        ]

    def get_output_object(self, variable: str) -> Output:
        """Creates a Dash Output object for a given variable.

        Use this if you need to have a module output back to the shared VariableSelector in the main layout.

        Args:
            variable (str): The variable name.

        Returns:
            Output: The corresponding Dash Output object.
        """
        if variable not in [option.title for option in self._variableselectoroptions]:
            raise ValueError(
                f"Invalid variable name, expected one of {[option.title for option in self._variableselectoroptions]}. Received {variable}"
            )
        option = self.get_option(variable)
        return Output(option.id, "value", allow_duplicate=True)

    def get_callback_args(self, inputs=False, states=False):
        args = []
        if inputs:
            False
        if states:
            False
        return args

    def _create_variable_card(
        self,
        text: str,
        component_id: str,
        input_type: str,
        value: str | int | float | None = None,
    ) -> dbc.Col:
        """Generate a Dash Bootstrap card with an input field.

        Args:
            text (str): The title text to display on the card.
            component_id (str): The ID to assign to the input field within the card.
            input_type (str): The type of the input field (e.g., "text", "number").
            value (str, optional): The default value for the input field. Defaults to an empty string.

        Returns:
            dbc.Col: A column containing the card with an input field.
        """
        if value is None:
            value = ""
        card = dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5(text, className="card-title"),
                        html.Div(
                            style={
                                "display": "grid",
                                "grid-template-columns": "100%",
                            },
                            children=[
                                dbc.Input(
                                    value=value, id=component_id, type=input_type
                                ),
                            ],
                        ),
                    ],
                    style={"max-height": "100%"},
                ),
                style={"max-height": "100%"},
            )
        )
        self._make_alert_callback(
            component_id, text
        )  # Should be made optional, maybe as an argument in main_layout
        return card

    def _make_alert_callback(self, component_id: str, component_name: str) -> Any:
        """Utility function to add alerts to updates on the variable selector."""

        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input(component_id, "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def alert_connection(
            value: Any, error_log: list[dict[str, Any]]
        ) -> list[dict[str, Any]]:
            """Alert callback connecting variable picker card to the alert handler."""
            error_log.append(
                create_alert(
                    f"Oppdatering av variabelvelger: {component_name} til {value}",
                    "info",
                    ephemeral=True,
                )
            )
            return error_log

        alert_connection.__name__ = f"alert_connection_{component_id}"
        return alert_connection

    def layout(
        self,
    ) -> list[dbc.Col]:
        """Generate a list of Dash Bootstrap cards based on selected variable keys."""
        if self.default_values is None:
            default_values = {}
        else:
            default_values = self.default_values
        layout = []
        for variable in self.selected_variables:
            option = self.get_option(variable)
            print(option)
            card = self._create_variable_card(
                text=option.title,
                component_id=option.id,
                input_type=option.type,
                value=default_values.get(option.title, None),
            )
            layout.append(card)
        return layout


class VariableSelectorOption:
    """Represents an individual variable selection option."""

    def __init__(self, variable_title: str, variable_type: str) -> None:
        """Initializes a VariableSelectorOption.

        After checking its own validity, adds itself as an option for the VariableSelector by appending itself into the VariableSelector._variableselectoroptions class variable.

        Args:
            variable_title (str): The name of the variable.
            variable_type (str): The type of the variable ("text" or "number").

        Examples:
            >>> VariableSelectorOption("my numeric option", "number")
            >>> VariableSelectorOption("my text option", "text")
        """
        self.title = variable_title
        self.id = f"var-{variable_title}"
        self.type = variable_type

        self.is_valid()

        VariableSelector._variableselectoroptions.append(self)

    def is_valid(self):
        """Validates the option before adding it to the list."""
        valid_types = ["text", "number"]
        if self.type not in valid_types:
            raise ValueError(
                f"Invalid value for variable_type. Expected one of {valid_types}, received {self.type}"
            )

    def __str__(self) -> str:
        """Returns a string representation of the variable option."""
        return f"Title: {self.title}\nId: {self.id}\nType: {self.type}\n"


"""Here we define some default values that are available from the get-go"""
# Periods
VariableSelectorOption("aar", "number")
VariableSelectorOption("termin", "number")
VariableSelectorOption("måned", "number")
# Groupings
VariableSelectorOption("nace", "text")
VariableSelectorOption("fylke", "text")
VariableSelectorOption("nspekfelt", "text")
VariableSelectorOption("prodcomkode", "text")
# Identifiers
VariableSelectorOption("oppgavegiver", "text")
VariableSelectorOption("foretak", "text")
VariableSelectorOption("bedrift", "text")
VariableSelectorOption("skjemaenhet", "text")
