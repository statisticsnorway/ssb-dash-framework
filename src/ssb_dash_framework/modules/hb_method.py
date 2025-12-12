# TODO: Rewrite to window/tab implementation model

import logging
from abc import abstractmethod
from collections.abc import Callable
from typing import Any
from typing import ClassVar

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate

from ..setup.variableselector import VariableSelector
from ..utils.implementations import TabImplementation
from ..utils.implementations import WindowImplementation
from ..utils.module_validation import module_validator
from ..utils.r_helpers import _get_kostra_r
from ..utils.r_helpers import hb_method

logger = logging.getLogger(__name__)


class HBMethod:
    """Module for implementing the HB method for finding outliers."""

    _id_number: ClassVar[int] = 0
    _required_variables: ClassVar[list[str]] = ["ident"]

    def __init__(
        self,
        get_data_func: Callable[..., Any],
        time_units: list[str],
        varselector_variable: str = "statistikkvariabel",
        output: str = "ident",
    ) -> None:
        """Initializes the HB method module.

        Args:
            get_data_func (Callable[..., Any]): A function that takes a time_variable as input and returns a dataframe. The dataframe MUST have the columns 'ident', 'variabel' and two columns containing the values from different times to compare.
            time_units (list[str]): A list of time units for the dataset. Example: ['year']
            varselector_variable (str): The name of the variableselector field used for determining which variable to analyze.
            output (str): Which variableselector field to update based on clicks in the graph.
        """
        logger.warning(
            "This module is still in development and most likely has issues. If you notice something strange, please add it to Issues on the github repo."
        )
        self.module_number = HBMethod._id_number
        self.module_name = self.__class__.__name__
        HBMethod._id_number += 1

        self.icon = "🥼"
        self.label = "HB metoden"
        self.variable: str | None = None

        self.variableselector = VariableSelector(
            selected_inputs=[], selected_states=[*time_units, varselector_variable]
        )
        logger.warning("Currently this module only supports year as time unit.")

        self.time_units = time_units
        self.varselector_variable = varselector_variable
        self.get_data_func = get_data_func
        self.get_default_parameter_values()
        self.ident = "ident"
        self.output = output

        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)
        _get_kostra_r()

    def get_default_parameter_values(self) -> None:
        """Gets the default parameter values."""
        # TODO make it possible to save params in a config somewhere
        self.pc = 20
        self.pu = 0.5
        self.pa = 0.05

    def make_hb_figure(self, time_unit: str, *args: Any) -> go.Figure:
        """Runs the HB method and creates the plot showing the results."""
        data = self.get_data_func(self.variable, time_unit)

        time_cols = sorted([x for x in data.columns if x not in ["ident", "variabel"]])
        if len(time_cols) > 2:
            raise ValueError(
                f"Too many columns in dataframe from get_data_func. Should be only 'ident', 'variabel' and two periods as separate columns. Received: {data.columns}"
            )
        _t_0 = time_cols[0]
        _t_1 = time_cols[1]

        data = hb_method(
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

    def _create_layout(self) -> dbc.Container:
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
                        ),
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
                        ),
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
                        ),
                    ]
                )
            ),
        ]

        layout = dbc.Container(
            children=[
                infobox,
                dbc.Row(
                    [
                        dbc.Col(
                            id=f"{self.module_number}-hb-selectedvariable",
                            children=html.P(
                                f"No selected variable. Check your {self.varselector_variable} field."
                            ),
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id=f"{self.module_number}-hb-dropdown",
                                options=self.time_units,
                                value=self.time_units[0],
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
                            dbc.Button("Åpne infoboks", id="open", n_clicks=0),
                        ),
                    ]
                ),
                dbc.Row(
                    [*inputs],
                ),
                html.Hr(),
                dbc.Row(
                    dcc.Loading(dcc.Graph(id=f"{self.module_number}-hb_figure")),
                ),
            ],
            fluid=True,
        )

        logger.debug("Generated layout")
        return layout

    def module_callbacks(self) -> None:
        """Registers the callbacks for the module."""

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-hb-selectedvariable", "children"),
            self.variableselector.get_input(self.varselector_variable),
        )
        def set_variable(varselector_variable_value: str) -> html.P:
            self.variable = varselector_variable_value
            return html.P(f"Selected variable: {varselector_variable_value}")

        @callback(  # type: ignore[misc]
            Input(f"{self.module_number}-hb_pc", "value"),
        )
        def update_pc(pc: int) -> None:
            self.pc = pc

        @callback(  # type: ignore[misc]
            Input(f"{self.module_number}-hb_pu", "value"),
        )
        def update_pu(pu: int) -> None:
            self.pu = pu

        @callback(  # type: ignore[misc]
            Input(f"{self.module_number}-hb_pa", "value"),
        )
        def update_pa(pa: int) -> None:
            self.pa = pa

        @callback(  # type: ignore[misc]
            Output(f"{self.module_number}-hb_figure", "figure"),
            Input(f"{self.module_number}-hb_button", "n_clicks"),
            State(f"{self.module_number}-hb-dropdown", "value"),
            self.variableselector.get_all_states(),
        )
        def calculate_hb(n_click: int | None, time_unit: str, *args: Any) -> go.Figure:
            if not n_click:
                raise PreventUpdate
            if self.variable is None:
                logger.info("Preventing update due to self.variable being 'None'.")
                raise PreventUpdate
            return self.make_hb_figure(time_unit, *args)

        @callback(  # type: ignore[misc]
            self.variableselector.get_output_object(self.ident),
            Input(f"{self.module_number}-hb_figure", "clickData"),
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

    @abstractmethod
    def layout(self) -> html.Div:
        """Define the layout for the HBMethod module.

        This is an abstract method that must be implemented by subclasses to define the module's layout.

        Returns:
            html.Div: A Dash HTML Div component representing the layout of the module.
        """
        pass


class HBMethodTab(TabImplementation, HBMethod):
    """Module for implementing the HB method for finding outliers, in a tab format."""

    def __init__(
        self,
        get_data_func: Callable[..., Any],
        time_units: list[str],
        varselector_variable: str = "statistikkvariabel",
        output: str = "ident",
    ) -> None:
        """Initializes the HB method module.

        Args:
            get_data_func (Callable[..., Any]): A function that takes a time_variable as input and returns a dataframe. The dataframe MUST have the columns 'ident', 'variabel' and two columns containing the values from different times to compare.
            time_units (list[str]): A list of time units for the dataset. Example: ['year']
            varselector_variable (str): The name of the variableselector field used for determining which variable to analyze.
            output (str): Which variableselector field to update based on clicks in the graph.
        """
        HBMethod.__init__(
            self,
            get_data_func=get_data_func,
            time_units=time_units,
            varselector_variable=varselector_variable,
            output=output,
        )
        TabImplementation.__init__(self)


class HBMethodWindow(WindowImplementation, HBMethod):
    """Module for implementing the HB method for finding outliers, in a window format."""

    def __init__(
        self,
        get_data_func: Callable[..., Any],
        time_units: list[str],
        varselector_variable: str = "statistikkvariabel",
        output: str = "ident",
    ) -> None:
        """Initializes the HB method module.

        Args:
            get_data_func (Callable[..., Any]): A function that takes a time_variable as input and returns a dataframe. The dataframe MUST have the columns 'ident', 'variabel' and two columns containing the values from different times to compare.
            time_units (list[str]): A list of time units for the dataset. Example: ['year']
            varselector_variable (str): The name of the variableselector field used for determining which variable to analyze.
            output (str): Which variableselector field to update based on clicks in the graph.
        """
        HBMethod.__init__(
            self,
            get_data_func=get_data_func,
            time_units=time_units,
            varselector_variable=varselector_variable,
            output=output,
        )
        WindowImplementation.__init__(
            self,
        )
