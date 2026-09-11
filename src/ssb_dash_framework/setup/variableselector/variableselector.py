import logging
from typing import Any, Literal, cast
from typing import ClassVar
import warnings

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import html
from dash.exceptions import PreventUpdate

from .time_unit import TimeUnit
from ...utils.alert_handler import AlertHandler

logger = logging.getLogger(__name__)

InputType = (
    Literal[
        "text",
        "number",
        "password",
        "email",
        "range",
        "search",
        "tel",
        "url",
        "hidden",
        "time",
    ]
    | None
)

def set_variables(variable_list: str | list[str]) -> None:
    """Sets the list of variables for the VariableSelector.

    Args:
        variable_list: List of variable names to be added to the VariableSelector.

    Raises:
        TypeError: If variable_list is not a string or a list of strings.

    Examples:
        >>> set_variables("orgnr")
        >>> set_variables("kvartal")
        >>> set_variables(["foretak", "aar"])
    """
    warnings.warn("'set_variables' feature is deprecated", DeprecationWarning)
    raise NotImplementedError(
        "set_variables if deprecated. Migrate to VariableSelectorConfig"
    )


class VariableSelector:
    """Class containing options for shared states between modules in the framework.

    Notes:
        - Each module should have its own instance of the VariableSelector in its __init__ function.
    """

    _variableselectoroptions: ClassVar[list["VariableSelectorOption"]] = []
    # _inputs: ClassVar[list[str]] = []
    # _states: ClassVar[list[str]] = []
    _refnr: ClassVar[str | None] = None
    _ident: ClassVar[str | None] = None
    _time_unit: ClassVar[None | TimeUnit] = None
    _secondary_ident: ClassVar[list[str] | None] = None
    _grouping_variables: ClassVar[list[str] | None] = None

    def __init__(
        self,
        selected_inputs: list[str],
        selected_states: list[str],
        default_values: dict[str, str | int | float] | None = None,
    ) -> None:
        """Initializes the VariableSelector class.

        Args:
            selected_inputs: List of selected input variable names. Will trigger callbacks.
            selected_states: List of selected state variable names. Will not trigger callbacks.
            default_values: Default values for variables. Defaults to None.

        Examples:
            >>> VariableSelector(selected_inputs = ["foretak"], selected_states = ["aar"])
            >>> VariableSelector(selected_inputs = ["foretak"], selected_states = ["aar"], default_values = {"aar": "2024"})

        Notes:
            - Usage in a module involves using the callback objects returned by either `get_all_inputs` and `get_all_states` or `get_callback_objects` to register callbacks.
            - The `get_output_object` method can be used to create an Output object updating the main VariableSelector in the app through a callback.
        """
        self.options = [option.title for option in self._variableselectoroptions]
        # self.inputs = selected_inputs
        # self.states = selected_states
        # VariableSelector._inputs = selected_inputs
        # VariableSelector._states = selected_states

        # self.selected_variables = [*selected_inputs, *selected_states]
        self.default_values = default_values

        self._is_valid()
        if default_values:
            self._default_values_is_valid()

    def _is_valid(self) -> None:
        """Ensures the VariableSelector is set up as intended."""
        # valid_states_inputs = [
        #    option.title for option in VariableSelector._variableselectoroptions
        # ]
        for _option in self._variableselectoroptions:
            if not isinstance(_option, VariableSelectorOption):
                raise TypeError(
                    f"Invalid type. Should only contain values of type VariableSelectorOption. Received type: {type(_option)}: {_option}"
                )

        # for _input in self.inputs:
        #    if _input not in valid_states_inputs:
        #        raise ValueError(
        #            f"Invalid value for selected_inputs. Received {_input}. Expected one of {valid_states_inputs}"
        #        )
        # for _state in self.states:
        #    if _state not in valid_states_inputs:
        #        raise ValueError(
        #            f"Invalid value for selected_states. Received {_state}. Expected one of {valid_states_inputs}"
        #        )

    def _default_values_is_valid(self) -> None:
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
                if not isinstance(self.default_values[key], int | float):
                    raise TypeError(
                        f"Invalid type for {key} in default_value. Received type {type(self.default_values[key])} Expected int or float."
                    )

    @classmethod
    def get_option(
        cls, search_term: str, search_target: str = "title"
    ) -> "VariableSelectorOption":
        """Retrieves a VariableSelectorOption by variable name.

        Args:
            search_term: Word to search for, needs to be an exact match.
            search_target: Element of VariableSelectorOption to search.

        Returns:
            VariableSelectorOption object matching description.

        Raises:
            ValueError: If 'search_target' is not a searchable property.
            Exception: If something goes wrong in a weird way.
        """
        if search_target not in ["title", "id"]:
            raise ValueError(
                f"'search_target' must be 'title' or 'id'. Received: {search_target}"
            )
        for option in cls._variableselectoroptions:
            if (search_target == "title" and option.title == search_term) or (
                search_target == "id" and option.id == search_term
            ):
                return option

        if search_target == "title":
            raise ValueError(
                f"ValueError: '{search_term}' not in list of options, expected one of {[x.title for x in cls._variableselectoroptions]}\nIf you need to add {search_term} to the available options, refer to the VariableSelectorOption docstring."
            )
        elif search_target == "id":
            raise ValueError(
                f"ValueError: '{search_term}' not in list of options, expected one of {[x.id for x in cls._variableselectoroptions]}\nIf you need to add {search_term} to the available options, refer to the VariableSelectorOption docstring."
            )
        else:
            raise RuntimeError(
                "No idea how you ended up here, please create an issue on our GitHub repository."
            )

    @classmethod
    def get_input(
        cls, requested: str | list[str], search_target: str = "title"
    ) -> list[Input]:
        """Retrieves a Input object for the selected variable."""
        if isinstance(requested, str):
            requested = [requested]

        inputs = []
        for var in requested:
            retrieved_option = cls.get_option(
                search_term=var, search_target=search_target
            )
            inputs.append(Input(retrieved_option.id, "value"))
        return inputs

    @classmethod
    def _match_type[T: (
        Input,
        State,
        Output,
    )](cls, var: str | None, _type: type[Input | State | Output]) -> T:
        if var is None:
            raise RuntimeError(
                f"You used a module that requested the variable '{var}'. This variable is not set in the VariableSelectorConfig"
            )

        if _type is Input:
            return cast(T, cls.get_input(var)[0])

        elif _type is State:
            return cast(T, cls.get_state(var))

        elif _type is Output:
            return cast(T, cls.get_output_object(var))
        else:
            raise RuntimeError(
                f"You used a module that requested the variable '{var}'. This variable is not set in the VariableSelectorConfig"
            )

    @classmethod
    def get_timevar[T: (
        Input,
        State,
        Output,
    )](cls, _type: type[Input | State | Output]) -> T:
        timevar = cls._time_unit
        if timevar is None:
            raise RuntimeError("Time unit is not set")
        return cls._match_type(timevar.name, _type=_type)

    @classmethod
    def get_refnr[T: (
        Input,
        State,
        Output,
    )](cls, _type: type[Input | State | Output]) -> T:
        refnr = cls._refnr
        return cls._match_type(refnr, _type=_type)

    @classmethod
    def get_ident[T: (
        Input,
        State,
        Output,
    )](cls, _type: type[Input | State | Output]) -> T:
        ident = cls._ident
        return cls._match_type(ident, _type=_type)

    @classmethod
    def get_secondary_ident[T: (
        Input,
        State,
        Output,
    )](cls, _type: type[Input | State | Output]) -> list[T]:
        secondary_idents = cls._secondary_ident
        if secondary_idents is None:
            secondary_idents = []

        return [cls._match_type(var, _type=_type) for var in secondary_idents]

    @classmethod
    def get_grouping_vars[T: (
        Input,
        State,
        Output,
    )](cls, _type: type[Input | State | Output]) -> list[T]:
        grouping_vars = cls._grouping_variables
        if grouping_vars is None:
            grouping_vars = []

        return [cls._match_type(var, _type=_type) for var in grouping_vars]

    # @classmethod
    # def get_all_inputs(cls) -> list[Input]:
    #    """Retrieves a list of Dash Input objects for selected inputs."""
    #    to_be_returned = [
    #        Input(option.id, "value")
    #        for input_title in cls._inputs
    #        for option in cls._variableselectoroptions
    #        if option.title == input_title
    #    ]
    #    logger.debug(f"Gettings inputs: {to_be_returned}")
    #    if len(to_be_returned) == 0:
    #        logger.debug(
    #            "Returning empty list of inputs. This is fine if intentional, but could cause weird bugs if not. Check this if something is missing from callbacks."
    #        )
    #    return to_be_returned

    @classmethod
    def get_state(cls, requested: str, search_target: str = "title") -> State:
        """Retrieves a State object for the selected variable."""
        retrieved_option = cls.get_option(
            search_term=requested, search_target=search_target
        )
        return State(retrieved_option.id, "value")

    # @classmethod
    # def get_all_states(cls) -> list[State]:
    #    """Retrieves a list of Dash State objects for selected states."""
    #    to_be_returned = [
    #        State(option.id, "value")
    #        for state_title in cls._states
    #        for option in cls._variableselectoroptions
    #        if option.title == state_title
    #    ]
    #    logger.debug(f"Gettings inputs: {to_be_returned}")
    #    if len(to_be_returned) == 0:
    #        logger.debug(
    #            "Returning empty list of states. This is fine if intentional, but could cause weird bugs if not. Check this if something is missing from callbacks."
    #        )
    #    return to_be_returned

    # @classmethod
    # def get_all_callback_objects(cls) -> list[Input | State]:
    #    """Retrieves a list of Dash Input and State objects for all selected variables."""
    #    to_be_returned = cls.get_all_inputs() + cls.get_all_states()
    #    logger.debug(f"Getting callback objects: {to_be_returned}")
    #    if len(to_be_returned) == 0:
    #        logger.debug(
    #            "Returning empty list of inputs and states. This is fine if intentional, but could cause weird bugs if not. Check this if something is missing from callbacks."
    #        )
    #    return to_be_returned

    @classmethod
    def get_output_object(cls, variable: str) -> Output:
        """Creates a Dash Output object for a given variable.

        Use this if you need to have a module output back to the shared VariableSelector in the main layout.

        Args:
            variable: The variable name.

        Returns:
            Output: The corresponding Dash Output object.

        Raises:
            ValueError: If the name (title) does not exist in any of the options available to the VariableSelector
        """
        if variable not in [option.title for option in cls._variableselectoroptions]:
            raise ValueError(
                f"Invalid variable name, expected one of {[option.title for option in cls._variableselectoroptions]}. Received {variable}"
            )
        option = cls.get_option(variable)
        output_object = Output(option.id, "value", allow_duplicate=True)
        logger.debug(f"Getting output object for {variable}: {output_object}")
        return output_object

    @classmethod
    def get_all_states(cls) -> list[State]:
        return [State(var.id, "value") for var in cls._variableselectoroptions]

    def _create_variable_card(
        self,
        text: str,
        component_id: str,
        input_type: InputType,
        value: str | int | float | None = None,
    ) -> dbc.Col:
        """Generate a Dash Bootstrap card with an input field.

        Args:
            text: The title text to display on the card.
            component_id: The ID to assign to the input field within the card.
            input_type: The type of the input field (e.g., "text", "number").
            value: The default value for the input field. Defaults to an empty string.

        Returns:
            dbc.Col: A column containing the card with an input field.
        """
        if value is None:
            value = ""
        card = dbc.Col(
            dbc.Card(
                className="variable-selector-card",
                children=dbc.CardBody(
                    className="variable-selector-cardbody",
                    children=[
                        html.H5(text, className="card-title"),
                        html.Div(
                            className="ssb-input",
                            children=[
                                dbc.Input(
                                    value=value,
                                    id=component_id,
                                    type=input_type,
                                ),
                            ],
                        ),
                    ],
                ),
            )
        )
        self._make_alert_callback(component_id, text)
        return card

    def _make_alert_callback(self, component_id: str, component_name: str) -> Any:
        """Utility function to add alerts to updates on the variable selector."""

        @callback(  # type: ignore[misc]
            Input(component_id, "value"),
            prevent_initial_call=True,
        )
        def alert_connection(value: Any) -> None:
            """Alert callback connecting variable picker card to the alert handler."""
            logger.info(
                f"Attempting to update variable selector: {component_name} to {value}"
            )
            if isinstance(value, str):
                AlertHandler.info(
                    f"Oppdatering av variabelvelger: {component_name} til {value}"
                )
            else:
                AlertHandler.warning(
                    f"Problem med oppdatering av {component_name} til {value}. Sjekk datatype, burde være string men mottok {type(value)}"
                )
                raise PreventUpdate

        alert_connection.__name__ = f"alert_connection_{component_id}"
        return alert_connection

    def layout(
        self,
    ) -> list[dbc.Row]:
        """Generate a list of Dash Bootstrap cards based on selected variable keys."""
        if self.default_values is None:
            default_values = {}
        else:
            default_values = self.default_values
        layout = []
        for variable in self._variableselectoroptions:
            print(variable)
            option = self.get_option(variable.title)
            card = self._create_variable_card(
                text=option.title,
                component_id=option.id,
                input_type=option.type,
                value=default_values.get(option.title, None),
            )
            layout.append(card)
        return layout


class VariableSelectorOption:  # TODO: Should maybe reverse the logic and have title mirror id instead of id mirror title.
    """Represents an individual variable selection option."""

    def __init__(
        self,
        variable_title: str,
        variable_id: str | None = None,
    ) -> None:
        """Initializes a VariableSelectorOption.

        After checking its own validity, adds itself as an option for the VariableSelector by appending itself into the VariableSelector._variableselectoroptions class variable.

        Args:
            variable_title: The name of the variable. This is the label you want to see in the app.
            variable_id: The id of the variable. This should be the name of the variable in your data. Defaults to be the supplied variable_title with a 'var-' prefix.

        Raises:
            ValueError: If the variable_id supplied starts with '-var'. This is added automatically during intialization.

        Examples:
            >>> VariableSelectorOption("fylke_nr")
            >>> VariableSelectorOption(variable_title="komm_nr")
            >>> VariableSelectorOption(variable_title="Organisasjonsnummer", variable_id="ident")
        """
        logger.debug(
            f"initializing VariableSelectorOption.\nvariable_title: {variable_title}\nvariable_id: {variable_id}"
        )
        if variable_id and variable_id.startswith("var-"):
            raise ValueError(
                "'var-' is automatically added to the id of this variable, remove it from the input."
            )
        self.title = variable_title
        self.id = f"var-{variable_id}" if variable_id else f"var-{variable_title}"
        self.type: InputType = "text"

        self._is_valid()

        logger.debug(f"Adding option to options list:\n{self}")

        VariableSelector._variableselectoroptions.append(self)

    def _is_valid(self) -> None:
        """Validates the option before adding it to the list."""
        self._already_exists()
        valid_types = [
            "text",
            "number",
            "password",
            "email",
            "range",
            "search",
            "tel",
            "url",
            "hidden",
            "time",
        ]
        if self.type not in valid_types:
            raise ValueError(
                f"Invalid value for variable_type. Expected one of {valid_types}, received {self.type}"
            )

    def _already_exists(self) -> None:
        """Checks if option already exists.

        Note: The check on self.id should not be necessary but is added as a precaution.
        """
        if self.title in [x.title for x in VariableSelector._variableselectoroptions]:
            raise ValueError(f"This option title already exists: {self.title}")
        if self.id in [x.id for x in VariableSelector._variableselectoroptions]:
            raise ValueError(
                f"This option id already exists and cannot be added: {self.id}"
            )

    def __str__(self) -> str:
        """Returns a string representation of the variable option."""
        return f"Title: {self.title}\nId: {self.id}\nType: {self.type}\n"
