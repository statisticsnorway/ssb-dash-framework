# TODO: Rewrite to window/tab implementation model

import logging
import time
from collections.abc import Callable
from typing import Any

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector
from ..utils import hb_method
from ..utils.functions import sidebar_button
from ..utils.module_validation import module_validator
from ..utils.r_helpers import _get_kostra_r, hb_method

logger = logging.getLogger(__name__)




class HBMethod:
    _id_number = 0
    _required_variables = ["ident"]
    def __init__(
        self,
        get_data_func,
        time_units: list[str],
        output = "ident"
    ):
        self.module_number = HBMethod._id_number
        self.module_name = self.__class__.__name__
        HBMethod._id_number += 1

        self.icon = ""
        self.label = "HB metoden"
        
        self.variableselector = VariableSelector(
            selected_inputs=time_units, selected_states=[]
        )
        logger.warning("Currently this module only supports year as time unit.")

        self.time_units = time_units
        self.get_data_func = get_data_func

        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)
        self.ident = "ident"
        self.get_default_parameter_values()
        _get_kostra_r()
    
    def get_default_parameter_values(self):
        # TODO make it possible to save params in a config somewhere
        self.pc = 20
        self.pu = 0.5
        self.pa = 0.05


    def make_hb_figure(self, time_unit):

        data = self.get_data_func(time_unit)

        data: pd.DataFrame = hb_method(
            data=data,
            p_c=self.pc,
            p_u=self.pu,
            p_a=self.pa,
            id_field_name=self.ident,
            x_1_field_name=_t_0,
            x_2_field_name=_t_1,
        ).sort_values(by=["maxX"])
        logger.debug("HB calculation done successfully.")
        x = data["maxX"]
        y = data["ratio"]
        z = data["upperLimit"]
        k = data["lowerLimit"]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                hovertext=data["id"],
                name="Observasjon",
                marker={
                    "color": data["outlier"],
                    "colorscale": [[0, "#3498DB"], [1, "yellow"]],
                },
            )
        )
        fig.add_trace(go.Scatter(x=x, y=z, name="Øvre grense", marker_color="red"))
        fig.add_trace(go.Scatter(x=x, y=k, name="Nedre grense", marker_color="red"))
        fig.update_layout(
            height=800,
            title_text="HB-metoden",
            plot_bgcolor="#1F2833",
            paper_bgcolor="#1F2833",
            font_color="white",
        )
        fig.update_xaxes(title=self.variable, range=[0, max(x) * 1.05])
        fig.update_yaxes(title="Forholdstallet")
        logger.debug("Done, returning fig")
        return fig

    def validate_hb_data(self):
        """Checks that the dataframe follows the correct structure for further processing."""
        ...
    
    def _create_layout(self):
        infobox = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("HB-metoden")),
                        dbc.ModalBody(
                            "Output: All units are returned, but the HB method is only performed on the data set where units with both x1 and x2 not missing and greater than zero are included. In this data set, units with x1 = x2 are included in he HB method only if they cover less than 50 per cent of the number of units in the stratum."
                        ),
                        dbc.ModalFooter(
                            html.Button(
                                "Lukk", id="close", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
                    id="modal",
                    is_open=False,
                ),
            ]
        )

        inputs = [
            dbc.Col(
                dbc.Stack(
                    [
                        html.Span(
                            children="Skriv inn pC",
                            id=f"{self.module_number}-hb_pc_text",
                        ),
                        dbc.Tooltip(
                            children=html.P(
                                "Parameter that controls the length of the confidence interval."
                            ),
                            target=f"{self.module_number}-hb_pc_text",
                        ),
                        dcc.Input(
                            id=f"{self.module_number}-hb_pc",
                            type="number",
                            value=self.pc,
                            min=0,
                        )
                    ]
                )
            ),
            dbc.Col(
                dbc.Stack(
                    [
                        html.Span(
                            children="Skriv inn pU",
                            id=f"{self.module_number}-hb_pu_text",
                        ),
                        dbc.Tooltip(
                            children=html.P(
                                "Parameter that adjusts for different level of the variables."
                            ),
                            target=f"{self.module_number}-hb_pu_text",
                        ),
                        dcc.Input(
                            id=f"{self.module_number}-hb_pu",
                            type="number",
                            value=self.pu,
                            min=0,
                            max=1,
                        )
                    ]
                )
            ),
            dbc.Col(
                dbc.Stack(
                    [
                        html.Span(
                            children="Skriv inn pA",
                            id=f"{self.module_number}-hb_pa_text",
                        ),
                        dbc.Tooltip(
                            children=html.P(
                                "Parameter that adjusts for small differences between the median and the 1st or 3rd quartile."
                            ),
                            target=f"{self.module_number}-hb_pa_text",
                        ),
                        dcc.Input(
                            id=f"{self.module_number}-hb_pa",
                            type="number",
                            value=self.pa,
                            min=0,
                            max=1,
                        )
                    ]
                )
            ),
        ]

        layout = html.Div(
            [
                                dbc.Row(infobox),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dcc.Dropdown(
                                                id = f"{self.module_number}-hb-dropdown"
                                                options = self.time_units,
                                                value = self.time_units[0]
                                            )
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Kjør HB-modell",
                                                id=f"{self.module_number}-hb_button",
                                                style={"height": "100%"},
                                            )
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Åpne infoboks", id="open", n_clicks=0
                                            ),
                                        ),
                                    ]
                                ),
                                dbc.Row(
                                    [
                                        *inputs
                                    ],
                                    style={"margin": "20px"},
                                ),
                                dbc.Row(
                                    dcc.Loading(dcc.Graph(id="hb_figure")),
                                    style={"margin": "20px"},
                                ),
                            ]
                        )     
        
        logger.debug("Generated layout")
        return layout
    
    def module_callbacks(self):
        @callback(
            Input(f"{self.module_number}-hb_pc", "value"),
        )
        def update_pc(pc):
            self.pc = pc
    
        @callback(
            Input(f"{self.module_number}-hb_pu", "value"),
        )
        def update_pc(pu):
            self.pu = pu
    
        @callback(
            Input(f"{self.module_number}-hb_pa", "value"),
        )
        def update_pc(pa):
            self.pa = pa

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-hb_figure", "figure"),
            Input(f"{self.module_number}-hb_button", "n_clicks"),
            State(f"{self.module_number}-hb-dropdown", "value"),
            self.variableselector.get_all_inputs()
        )
        def calculate_hb(n_click, time_unit, *args):
            return self.make_hb_figure(time_unit, *args)

        @callback(  # type: ignore[misc]
            self.variableselector.get_output_object(self.ident),
            Input("hb_figure", "clickData"),
            prevent_initial_call=True,
        )
        def hb_to_varselector(clickdata: dict[str, list[dict[str, Any]]]) -> str:
            """Passes the selected observation identifier to `variabelvelger`.

            Args:
                clickdata (dict): Data from the clicked point in the HB visualization.

            Returns:
                str: Identifier of the selected observation.

            Raises:
                PreventUpdate: if clickdata is None.
            """
            if not clickdata:
                raise PreventUpdate
            ident = str(clickdata["points"][0]["hovertext"])
            logger.info(f"Transfering {ident} to {self.ident}")
            return ident

   # @abstractmethod
    def layout(self) -> html.Div:
        """Define the layout for the HBMethod module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass

    

class HBMethodOld:
    """Module for detecting outliers using the Hidiroglou-Berthelot (HB) method in a Dash application.

    This module applies the HB method to identify potential outliers in time-series data by comparing
    values in the current period (t) with revised values from the previous period (t-1). It includes
    methods for preprocessing data, visualizing results, and managing interactions in a Dash app.

    Attributes:
        database (object): Database connection or interface for fetching data.
        hb_get_data (callable): Function for retrieving data based on selected parameters.

    References:
        More information about the HB method:
        https://rdrr.io/github/statisticsnorway/Kostra/man/Hb.html
    """


    def __init__(
        self,
        database: object,
        hb_get_data_func: Callable[..., pd.DataFrame],
        selected_state_keys: list[str],
        selected_ident: str,
        variable: str,
    ) -> None:
        """Initializes the HBMethodModule.

        Args:
            database (object): Database connection or interface to fetch relevant data.
            hb_get_data_func (Callable): Function to fetch data for processing using the HB method.
            selected_state_keys (list of str): Keys representing selected states for filtering data.
            selected_ident (str): Identifier used for grouping or unique identification in the data.
            variable (str): Name of the value variable to analyze using the HB method.
        """
        self.selected_ident = selected_ident
        self.variable = variable
        self.database = database
        self.hb_get_data = hb_get_data_func
        self._is_valid()  # Needs to happen before VariableSelector

        self.variableselector = VariableSelector([selected_ident], selected_state_keys)
        self.callbacks()

    def _is_valid(self) -> None:
        if not isinstance(self.selected_ident, str):
            raise ValueError(
                f"selected_ident should be type str, received {type(self.selected_ident)}"
            )

    def make_hb_data(
        self,
        data_df: pd.DataFrame,
        pc: int,
        pu: float,
        pa: float,
        ident: str,
        variable: str,
    ) -> pd.DataFrame:
        """Processes data using the HB method for outlier detection.

        Args:
            data_df (pandas.DataFrame): Input data containing variables for analysis.
            pc (int): Confidence interval control parameter.
            pu (float): Parameter for adjusting the variable's level.
            pa (float): Parameter for small differences between quartiles and the median.
            ident (str): Identifier field name in the dataset.
            variable (str): Name of the value variable for analysis.

        Returns:
            pandas.DataFrame: Processed data with outlier results, sorted by "maxX".
        """
        hb_result: pd.DataFrame = hb_method(
            data=data_df,
            p_c=pc,
            p_u=pu,
            p_a=pa,
            id_field_name=self.selected_ident,
            x_1_field_name=self.variable,
            x_2_field_name=f"{self.variable}_1",
        )
        logger.debug("Done, returning data")
        return hb_result.sort_values(by=["maxX"])

    def make_hb_figure(self, data: pd.DataFrame) -> go.Figure:
        """Creates a Plotly figure for visualizing HB method results.

        Args:
            data (pandas.DataFrame): Processed data from the HB method, including outlier and limit values.

        Returns:
            plotly.graph_objects.Figure: Plotly figure with scatter plots for observations and limits.
        """
        x = data["maxX"]
        y = data["ratio"]
        z = data["upperLimit"]
        k = data["lowerLimit"]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                hovertext=data["id"],
                name="Observasjon",
                marker={
                    "color": data["outlier"],
                    "colorscale": [[0, "#3498DB"], [1, "yellow"]],
                },
            )
        )
        fig.add_trace(go.Scatter(x=x, y=z, name="Øvre grense", marker_color="red"))
        fig.add_trace(go.Scatter(x=x, y=k, name="Nedre grense", marker_color="red"))
        fig.update_layout(
            height=800,
            title_text="HB-metoden",
            plot_bgcolor="#1F2833",
            paper_bgcolor="#1F2833",
            font_color="white",
        )
        fig.update_xaxes(title=self.variable, range=[0, max(x) * 1.05])
        fig.update_yaxes(title="Forholdstallet")
        logger.debug("Done, returning fig")
        return fig

    def layout(self) -> html.Div:
        """Generates the layout for the HB method Dash component.

        Returns:
            dash.html.Div: Div containing the modal and interactive elements for the HB method.
        """
        infobox = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("HB-metoden")),
                        dbc.ModalBody(
                            "Output: All units are returned, but the HB method is only performed on the data set where units with both x1 and x2 not missing and greater than zero are included. In this data set, units with x1 = x2 are included in he HB method only if they cover less than 50 per cent of the number of units in the stratum."
                        ),
                        dbc.ModalFooter(
                            html.Button(
                                "Lukk", id="close", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
                    id="modal",
                    is_open=False,
                ),
            ]
        )

        layout = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("HB-metoden")),
                        dbc.ModalBody(
                            [
                                dbc.Row(infobox),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                "Kjør HB-modell",
                                                id="hb_button",
                                                style={"height": "100%"},
                                            )
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Åpne infoboks", id="open", n_clicks=0
                                            ),
                                        ),
                                    ]
                                ),
                                dbc.Row(
                                    [
                                        self._build_input_field(
                                            "Skriv inn pC",
                                            "hb_pc",
                                            20,
                                            0,
                                            None,
                                            20,
                                            "Parameter that controls the length of the confidence interval.",
                                        ),
                                        self._build_input_field(
                                            "Skriv inn pU",
                                            "hb_pu",
                                            0.5,
                                            0,
                                            1,
                                            0.5,
                                            "Parameter that adjusts for different level of the variables.",
                                        ),
                                        self._build_input_field(
                                            "Skriv inn pA",
                                            "hb_pa",
                                            0.05,
                                            0,
                                            1,
                                            0.05,
                                            "Parameter that adjusts for small differences between the median and the 1st or 3rd quartile.",
                                        ),
                                    ],
                                    style={"margin": "20px"},
                                ),
                                dbc.Row(
                                    dcc.Loading(dcc.Graph(id="hb_figure")),
                                    style={"margin": "20px"},
                                ),
                            ]
                        ),
                    ],
                    id="hb-modal",
                    size="xl",
                    fullscreen="xxl-down",
                ),
                sidebar_button("🥼", "HB-Metoden", "sidebar-hb-button"),
            ]
        )
        logger.debug("Generated layout")
        return layout

    def _build_input_field(
        self,
        label: str,
        id_name: str,
        default_value: int | float,
        min_value: int | float,
        max_value: int | float | None,
        initial_value: int | float,
        tooltip_text: str,
    ) -> dbc.Col:
        """Builds an input field with a tooltip for user parameter inputs.

        Args:
            label (str): Text label for the input field.
            id_name (str): Unique ID for the input field.
            default_value (int | float): Default value for the input.
            min_value (int | float): Minimum allowable value.
            max_value (int | float): Maximum allowable value.
            initial_value (int | float): Initial value to display.
            tooltip_text (str): Text description displayed in the tooltip.

        Returns:
            dash_bootstrap_components.Col: Dash Bootstrap column containing the input field and tooltip.
        """
        return dbc.Col(
            dbc.Stack(
                [
                    html.Span(
                        label,
                        id=f"{id_name}_tooltip",
                        style={
                            "textDecoration": "underline",
                            "cursor": "pointer",
                            "color": "white",
                        },
                    ),
                    dbc.Tooltip(
                        [
                            html.P(tooltip_text),
                        ],
                        target=f"{id_name}_tooltip",
                    ),
                    dcc.Input(
                        id=id_name,
                        type="number",
                        value=default_value,
                        min=min_value,
                        max=max_value,
                    ),
                ]
            )
        )

    def callbacks(self) -> None:
        """Registers callbacks for the HB method Dash app components.

        Notes:
            This method registers Dash callbacks for handling user interactions, including
            running the HB method, toggling the modal, and passing results to `variabelvelger`.
        """
        time.time()

        dynamic_states = self.variableselector.get_all_states()
        output_object = self.variableselector.get_output_object(
            variable=self.selected_ident
        )
        #        output_object = Output(component_id, property_name, allow_duplicate=True)

        @callback(  # type: ignore[misc]
            Output("hb_figure", "figure"),
            Input("hb_button", "n_clicks"),
            State("hb_pc", "value"),
            State("hb_pu", "value"),
            State("hb_pa", "value"),
            *dynamic_states,
        )
        def use_hb(
            n_click: int, pc: int, pu: float, pa: float, *dynamic_states: list[Any]
        ) -> go.Figure:
            """Executes the HB method and updates the visualization.

            Args:
                n_click (int): Number of clicks on the "Run HB Model" button.
                pc (int): Confidence interval parameter.
                pu (float): Parameter for variable level adjustment.
                pa (float): Parameter for small differences between quartiles and the median.
                *dynamic_states (list): Additional state parameters for data filtering.

            Returns:
                plotly.graph_objects.Figure: Updated figure visualizing HB method results.

            Raises:
                PreventUpdate: If no button click is detected.
            """
            start_time = time.time()

            states_values = dynamic_states[: len(self.variableselector.states)]
            state_params = {
                key: value
                for key, value in zip(
                    self.variableselector.states, states_values, strict=False
                )
            }

            args: list[Any] = []
            for key in self.variableselector.states:
                var = state_params.get(key)
                if var is not None:
                    args.append(var)

            if "nace" in state_params and state_params["nace"] is not None:
                n = len(state_params["nace"])
                args.append(
                    n
                )  # TODO: Hva gjør dette egentlig? Burde omformuleres/dokumenteres

            if n_click:
                data = self.hb_get_data(
                    self.database, *args
                )  # *args må forklares, kanskje denne biten burde bli refactored?
                data = self.make_hb_data(
                    data, pc, pu, pa, self.selected_ident, self.variable
                )
                end_time = time.time()
                return self.make_hb_figure(data)
            else:
                raise PreventUpdate

        @callback(  # type: ignore[misc]
            Output("hb-modal", "is_open"),
            Input("sidebar-hb-button", "n_clicks"),
            State("hb-modal", "is_open"),
        )
        def hbmodal_toggle(n: int, is_open: bool) -> bool:
            """Toggles the state of the modal window.

            Args:
                n (int): Number of clicks on the toggle button.
                is_open (bool): Current state of the modal (open/closed).

            Returns:
                bool: New state of the modal (open/closed).
            """
            logger.info("Toggle modal")
            if n:
                return not is_open
            return is_open

        @callback(  # type: ignore[misc]
            output_object,
            Input("hb_figure", "clickData"),
            prevent_initial_call=True,
        )
        def hb_to_main_table(clickdata: dict[str, list[dict[str, Any]]]) -> str:
            """Passes the selected observation identifier to `variabelvelger`.

            Args:
                clickdata (dict): Data from the clicked point in the HB visualization.

            Returns:
                str: Identifier of the selected observation.

            Raises:
                PreventUpdate: if clickdata is None.
            """
            if not clickdata:
                raise PreventUpdate
            ident = str(clickdata["points"][0]["hovertext"])
            logger.info(f"Transfering {ident} to {self.selected_ident}")
            return ident

        logger.debug("Generated callbacks")

HBMethodWindow = HBMethod
