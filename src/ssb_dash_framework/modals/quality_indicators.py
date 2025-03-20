import logging
from collections.abc import Callable
from typing import Any

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate

from ..control.framework import QualityReport
from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)


class QualityIndicator:
    """A module for setting up the view for selected quality indicators.

    Attributes:
        indicators (list): A list of quality indicators.
            Example: [QualityIndicatorEditeringsandel(), QualityIndicatorEffektaveditering()]

    Notes:
        All indicators assume a long format for the data with a minimum of
        `ident`, `variabel`, and `verdi` as columns.
    """

    def __init__(self, indicators: list[Any]) -> None:
        """Initializes the quality indicator module with all selected indicators.

        Args:
            indicators (list): A list of quality indicator class objects.

        Raises:
            TypeError: If provided indicator does not have the attribute 'card'.
        """
        for indicator in indicators:
            if not hasattr(indicator, "card"):
                raise TypeError(
                    f"Object '{type(indicator)}' has no attribute 'card', which is necessary for the indicator to be rendered in the layout."
                )
        self.indicators = indicators
        self.callbacks()

    def layout(self) -> html.Div:
        """Creates the layout for the quality indicator modal.

        Returns:
            html.Div: A Dash HTML Div element containing the modal and the sidebar button.
        """
        return html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader([dbc.ModalTitle("kvalitetsindikatorer")]),
                        dbc.ModalBody(
                            [
                                html.Div(
                                    [indicator.card for indicator in self.indicators],
                                    style={
                                        "display": "grid",
                                        "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))",
                                        "gridGap": "20px",
                                    },
                                )
                            ]
                        ),
                    ],
                    id="kvalitetsindikatorer-modal",
                    size="xl",
                    fullscreen="xxl-down",
                ),
                sidebar_button(
                    "🎯", "Quality indicators", "sidebar-kvalitetsindikatorer-button"
                ),
            ]
        )

    def callbacks(self) -> None:
        """Registers callbacks to enable the modal to be opened and closed."""

        @callback(  # type: ignore[misc]
            Output("kvalitetsindikatorer-modal", "is_open"),
            Input("sidebar-kvalitetsindikatorer-button", "n_clicks"),
            State("kvalitetsindikatorer-modal", "is_open"),
        )
        def kvalitetsindikatorermodal_toggle(n: int, is_open: bool) -> bool:
            """Toggles the modal's open state.

            Args:
                n (int): Number of times the sidebar button has been clicked.
                is_open (bool): The current state of the modal (True for open, False for closed).

            Returns:
                bool: The new state of the modal.
            """
            if n:
                return not is_open
            return is_open


class QualityIndicatorEditeringsandel:
    """Quality indicator for editing ratio.

    Attributes:
        get_current_data_func (Callable): Function to retrieve current data.
        get_change_data_func (Callable): Function to retrieve rows with changes.
        periode: Current period for the data.
        var_name (str): The name of the column in the dataset indicating the variable.
        ident_var (str): Name of the identification variable. For example, "orgf".
        grouping_vars (list[str]): Variables by which the dataset can be grouped, such as "nace" or "kommune".
        key_vars (list[str]): Key variables relevant to the quality indicator.
    """

    def __init__(
        self,
        get_current_data_func: Callable[..., pd.DataFrame],
        get_change_data_func: Callable[..., pd.DataFrame],
        var_name: str,
        ident_var: str,
        grouping_vars: list[str] | None = None,
        key_vars: list[str] | None = None,
    ) -> None:
        """Initializes the editing ratio view for the quality indicator modal.

        Args:
            get_current_data_func (Callable): Function to retrieve current data.
            get_change_data_func (Callable): Function to retrieve rows with changes.
            var_name (str): Name of the variable column in the dataset.
            ident_var (str): Name of the identification variable.
            grouping_vars (list[str], optional): Variables for dataset grouping. Defaults to None.
            key_vars (list[str], optional): Key variables for the indicator. Defaults to None.
        """
        self.ident_var = ident_var
        self.var_name = var_name
        self.grouping_vars = grouping_vars if grouping_vars else []
        self.get_current_data = get_current_data_func
        self.get_change_data = get_change_data_func
        if key_vars:
            self.key_vars = key_vars  # TODO

        self.callbacks()

        self.card = html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H5("1 - Editeringsandel", className="card-title"),
                                dcc.Graph(
                                    figure=go.Figure(
                                        go.Indicator(
                                            mode="number+delta",
                                            value=self.editeringsandel(),
                                            number={"prefix": ""},
                                            # delta={"position": "bottom", "reference": self.editeringsandel(self.periode-1)}, # TODO
                                            domain={"x": [0, 1], "y": [0, 1]},
                                        )
                                    ).update_layout(
                                        height=150,
                                        margin=dict(l=20, r=20, t=20, b=20),
                                    ),
                                    config={"displayModeBar": False},
                                ),
                            ]
                        ),
                        dbc.CardFooter(
                            dbc.Button(
                                "Detaljer",
                                id="kvalitet-editeringsandel-button-details",
                            )
                        ),
                    ],
                    style={
                        "width": "18rem",
                        "margin": "10px",
                    },
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader("1 - Editeringsandel"),
                        dbc.ModalBody(
                            [
                                html.Div(
                                    children=[
                                        dcc.Dropdown(
                                            id="kvalitet-editeringsandel-dropdown",
                                            options=[
                                                {"label": x, "value": x}
                                                for x in [var_name, *self.grouping_vars]
                                            ],
                                        )
                                    ],
                                ),
                                dcc.Loading(
                                    id="kvalitet-editeringsandel-details",
                                ),
                            ]
                        ),
                    ],
                    id="editeringsandel-modal",
                ),
            ]
        )

    def editeringsandel(self) -> float:
        """Calculates the editing ratio.

        Returns:
            float: The editing ratio as a percentage.
        """
        total = pd.DataFrame(self.get_current_data().agg({self.ident_var: "nunique"}))
        changes = pd.DataFrame(self.get_change_data().agg({self.ident_var: "nunique"}))
        return float((changes / total * 100).iloc[0][0])

    def editeringsandel_details(self, group: list[str] | str) -> pd.DataFrame:
        """Calculates the editing ratio for different subsets of the dataset.

        Args:
            group (list[str] | str): Variable(s) by which to group the dataset.

        Returns:
            pd.DataFrame: A DataFrame with editing ratios for each subset.
        """
        if isinstance(group, str):
            group = [group]
        total = (
            self.get_current_data()
            .groupby(group)
            .agg({self.ident_var: "nunique"})
            .rename(columns={self.ident_var: "units"})
        )
        changes = (
            self.get_change_data()
            .groupby(group)
            .agg({self.ident_var: "nunique"})
            .rename(columns={self.ident_var: "edited_units"})
        )
        c = pd.merge(total, changes, on=group, how="left").fillna(0)
        c["editeringsandel"] = c["edited_units"] / c["units"] * 100
        return c.reset_index()

    def callbacks(self) -> None:
        """Sets up callbacks for opening the detail view and selecting grouping for details."""

        @callback(  # type: ignore[misc]
            Output("editeringsandel-modal", "is_open"),
            Input("kvalitet-editeringsandel-button-details", "n_clicks"),
            State("editeringsandel-modal", "is_open"),
        )
        def kvalitetediteringsandel_modaltoggle(n: int, is_open: bool) -> bool:
            """Toggles the detail view for the editing ratio.

            Args:
                n (int): Number of times the "Detaljer" button has been clicked.
                is_open (bool): Current state of the modal.

            Returns:
                bool: New state of the modal (True for open, False for closed).
            """
            if n:
                return not is_open
            return is_open

        @callback(  # type: ignore[misc]
            Output("kvalitet-editeringsandel-details", "children"),
            Input("kvalitet-editeringsandel-dropdown", "value"),
        )
        def editeringsandel_detailed(grouping_var: str) -> dcc.Graph:
            """Calculates detailed editing ratios for the selected grouping.

            Args:
                grouping_var (str): The grouping variable for detailed calculations.

            Returns:
                dcc.Graph: A bar chart displaying editing ratios by grouping.

            Raises:
                PreventUpdate: If no grouping_var the callback doesn't trigger.
            """
            if grouping_var:
                detail_data = self.editeringsandel_details(grouping_var)
                return dcc.Graph(
                    figure=px.bar(
                        detail_data,
                        x="editeringsandel",
                        y=grouping_var,
                        orientation="h",
                    )
                )
            else:
                raise PreventUpdate


class QualityIndicatorKontrollutslagsandel:
    """Indicator for displaying the percentage of possible control outcomes that trigger a flag.

    The control documentation must be a dataset with the following columns:
    `kontroll_id`, `Enheter kontrollert`, `Kontrollutslag`.

    Attributes:
        control_documentation (QualityReport | None): The quality report used for calculations.
        qualityreport_path (str | None): File path to a saved quality report in JSON format on Dapla.
    """

    def __init__(
        self,
        control_documentation: QualityReport | None = None,
        qualityreport_path: str | None = None,
    ) -> None:
        """Initializes the control outcome ratio view for the quality indicator modal.

        Args:
            control_documentation (QualityReport | None): A quality report for calculation.
            qualityreport_path (str | None): File path to a saved quality report in JSON format.

        Raises:
            ValueError: If both `control_documentation` and `qualityreport_path` are defined,
                        or if neither is provided.
        """
        if qualityreport_path and control_documentation:
            raise ValueError(
                "Remove either control_documentation or qualityreport_path. QualityIndicatorTreffsikkerhet() requires that only one of control_documentation and qualityreport_path is defined. If both are defined, it will not work."
            )
        if qualityreport_path:
            import json

            import dapla as dp

            with dp.FileClient.gcs_open(qualityreport_path, "r") as outfile:
                data = json.load(outfile)
            self.control_documentation = (
                pd.DataFrame(data["control_documentation"])
                .T.reset_index()
                .rename(columns={"index": "kontroll_id"})
            )
        elif control_documentation:
            self.control_documentation = control_documentation
        else:
            raise ValueError(
                "Either control_documentation or qualityreport_path needs to have a value."
            )
        self.kontrollutslagsandel_total, self.kontrollutslagsandel_detaljer = (
            self.kontrollutslag()
        )

        self.callbacks()

        self.card = html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H5(
                                    "2 - Kontrollutslagsandel", className="card-title"
                                ),
                                dcc.Graph(
                                    figure=go.Figure(
                                        go.Indicator(
                                            mode="number+delta",
                                            value=self.kontrollutslagsandel_total,
                                            number={"prefix": ""},
                                            # delta={"position": "bottom", "reference": self.editeringsandel(self.periode-1)}, # TODO
                                            domain={"x": [0, 1], "y": [0, 1]},
                                        )
                                    ).update_layout(
                                        height=150,
                                        margin=dict(l=20, r=20, t=20, b=20),
                                    ),
                                    config={"displayModeBar": False},
                                ),
                            ]
                        ),
                        dbc.CardFooter(
                            dbc.Button(
                                "Detaljer",
                                id="kvalitet-kontrollutslagsandel-button-details",
                            )
                        ),
                    ],
                    style={
                        "width": "18rem",
                        "margin": "10px",
                    },
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader("2 - Kontrollutslagsandel"),
                        dbc.ModalBody(
                            [
                                html.Div(
                                    children=[
                                        dag.AgGrid(
                                            columnDefs=[
                                                {"field": x}
                                                for x in self.kontrollutslagsandel_detaljer[
                                                    [
                                                        "kontroll_id",
                                                        "kontrollutslagsandel",
                                                        "Enheter kontrollert",
                                                        "Kontrollutslag",
                                                    ]
                                                ].columns
                                            ],
                                            rowData=self.kontrollutslagsandel_detaljer[
                                                [
                                                    "kontroll_id",
                                                    "kontrollutslagsandel",
                                                    "Enheter kontrollert",
                                                    "Kontrollutslag",
                                                ]
                                            ].to_dict("records"),
                                        )
                                    ],
                                ),
                                dcc.Loading(
                                    id="kvalitet-kontrollutslagsandel-details",
                                ),
                            ]
                        ),
                    ],
                    id="kontrollutslagsandel-modal",
                ),
            ]
        )

    def kontrollutslag(self) -> tuple[float, pd.DataFrame]:
        """Calculates the proportion of control outcomes that trigger a flag.

        Returns:
            tuple[float, pd.DataFrame]:
                - The total proportion of control outcomes as a float.
                - A DataFrame with detailed proportions for each control.
        """
        total = (
            self.control_documentation["Kontrollutslag"].sum()
            / self.control_documentation["Enheter kontrollert"].sum()
        )

        self.control_documentation["kontrollutslagsandel"] = (
            self.control_documentation["Kontrollutslag"]
            / self.control_documentation["Enheter kontrollert"]
        )

        return total, self.control_documentation

    def callbacks(self) -> None:
        """Sets up callbacks for opening and closing the detailed view."""

        @callback(  # type: ignore[misc]
            Output("kontrollutslagsandel-modal", "is_open"),
            Input("kvalitet-kontrollutslagsandel-button-details", "n_clicks"),
            State("kontrollutslagsandel-modal", "is_open"),
        )
        def kvalitetkontrollutslagsandel_modaltoggle(n: int, is_open: bool) -> bool:
            """Toggles the modal with control outcome details.

            Args:
                n (int): Number of clicks on the "Detaljer" button.
                is_open (bool): Current state of the modal.

            Returns:
                bool: New state of the modal (True for open, False for closed).
            """
            if n:
                return not is_open
            return is_open


class QualityIndicatorEffektaveditering:
    """Indicator to display the effect of editing.

    Attributes:
        get_current_data_func (Callable): Function to fetch the current updated data.
        get_original_data_func (Callable): Function to fetch the original received data.
        periode (str | int): The period for the data.
        ident_var (str): Name of the identification variable, e.g., "orgf".
        key_vars (list[str]): List of key variables relevant to the indicator.
        grouping_vars (list[str]): List of grouping variables for stratification.
    """

    def __init__(
        self,
        get_current_data_func: Callable[..., pd.DataFrame],
        get_original_data_func: Callable[..., pd.DataFrame],
        periode: str | int,  # TODO sjekk dette
        ident_var: str,
        key_vars: list[str],
        grouping_vars: str | list[str],
    ) -> None:
        """Initializes the view for the effect of editing in the quality indicator modal.

        Args:
            get_current_data_func (Callable): Function to fetch the current updated data.
            get_original_data_func (Callable): Function to fetch the original received data.
            periode (str | int): The period for the data.
            ident_var (str): Name of the identification variable.
            key_vars (list[str]): Key variables for the indicator.
            grouping_vars (list[str]): Grouping variables for stratification.
        """
        self.get_current_data = get_current_data_func
        self.get_original_data = get_original_data_func
        self.periode = periode
        self.ident_var = ident_var
        self.key_vars = key_vars
        if isinstance(grouping_vars, str):
            grouping_vars = [grouping_vars]
        self.grouping_vars = grouping_vars if grouping_vars else []

        self.callbacks()

        self.card = html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H5(
                                    "4 - Effekten av editering", className="card-title"
                                ),
                                dcc.Graph(
                                    figure=go.Figure(
                                        go.Indicator(
                                            mode="number+delta",
                                            value=self.get_comparison_data(
                                                self.periode
                                            )["effekt av editering"][0],
                                            number={"prefix": ""},
                                            # delta={"position": "bottom", "reference": self.editeringsandel(self.periode-1)}, # TODO
                                            domain={"x": [0, 1], "y": [0, 1]},
                                        )
                                    ).update_layout(
                                        height=150,
                                        margin=dict(l=20, r=20, t=20, b=20),
                                    ),
                                    config={"displayModeBar": False},
                                ),
                            ]
                        ),
                        dbc.CardFooter(
                            dbc.Button(
                                "Detaljer",
                                id="kvalitet-effekt-button-details",
                            )
                        ),
                    ],
                    style={
                        "width": "18rem",
                        "margin": "10px",
                    },
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader("4 - Effekten av editering"),
                        dbc.ModalBody(
                            [
                                html.Div(
                                    children=[
                                        dcc.Dropdown(
                                            id="kvalitet-effekt-dropdown",
                                            options=[
                                                {"label": x, "value": x}
                                                for x in [*grouping_vars]
                                            ],
                                        )
                                    ],
                                ),
                                dcc.Loading(
                                    id="kvalitet-effekt-details",
                                ),
                            ]
                        ),
                    ],
                    id="effekt-modal",
                ),
            ]
        )

    def get_comparison_data(
        self, periode: str | int, grouping: str | list[str] | None = None
    ) -> pd.DataFrame:
        """Calculates the effect of editing using the provided functions.

        Args:
            periode (str | int): The period for the data.
            grouping (list[str] | None): Variables for grouping. Defaults to None.

        Returns:
            pd.DataFrame: A DataFrame containing the calculated effect of editing.
        """
        if grouping is None:
            grouping = []
        elif isinstance(grouping, str):
            grouping = [grouping]
        edited = (
            self.get_current_data()
            .melt(id_vars=[self.ident_var, *grouping], value_vars=self.key_vars)
            .groupby([*grouping, "variable"])
            .agg({"value": "sum"})
            .rename(columns={"value": "editert"})
            .reset_index()
        )

        ueditert = (
            self.get_original_data()
            .melt(id_vars=[self.ident_var, *grouping], value_vars=self.key_vars)
            .groupby([*grouping, "variable"])
            .agg({"value": "sum"})
            .rename(columns={"value": "ueditert"})
            .reset_index()
        )

        merged = edited.merge(ueditert, on=[*grouping, "variable"])

        merged["effekt av editering"] = (
            (merged["ueditert"] - merged["editert"]) / merged["editert"] * 100
        )

        return merged

    def callbacks(self) -> None:
        """Sets up callbacks for opening and closing the detailed view."""

        @callback(  # type: ignore[misc]
            Output("effekt-modal", "is_open"),
            Input("kvalitet-effekt-button-details", "n_clicks"),
            State("effekt-modal", "is_open"),
        )
        def kvaliteteffekt_modaltoggle(n: int, is_open: bool) -> bool:
            """Toggles the modal displaying detailed information for the indicator.

            Args:
                n (int): Number of clicks on the "Detaljer" button.
                is_open (bool): Current state of the modal.

            Returns:
                bool: New state of the modal (True for open, False for closed).
            """
            if n:
                return not is_open
            return is_open

        @callback(  # type: ignore[misc]
            Output("kvalitet-effekt-details", "children"),
            Input("kvalitet-effekt-dropdown", "value"),
        )
        def kvalitet_effekt_detailed(grouping_var: str | None) -> dcc.Graph:
            """Computes the indicator per group for the selected grouping variable.

            Args:
                grouping_var (str | None): The selected grouping variable.

            Returns:
                dcc.Graph: A bar chart displaying the effect of editing for each group.

            Raises:
                PreventUpdate: If no grouping_var the callback doesn't trigger.
            """
            if grouping_var:
                detail_data = self.get_comparison_data(self.periode, grouping_var)
                return dcc.Graph(
                    figure=px.bar(
                        detail_data,
                        x="effekt av editering",
                        y=grouping_var,
                        orientation="h",
                    )
                )
            else:
                raise PreventUpdate


class QualityIndicatorTreffsikkerhet:
    """Indicator to display the accuracy of the controls being run.

    Attributes:
        get_edits_list_func (Callable):
            Function that retrieves a list of changes made to the data.
            It returns a list of tuples describing the fields changed.
            Used to check against control outcomes to determine if a control outcome
            likely resulted in an edit.
            Example: [(orgnr_1, variabel_1), (orgnr_1, variabel_2), (orgnr_2, variabel_1)].
        quality_report (QualityReport | None):
            The quality report used for calculations.
        qualityreport_path (str | None):
            File path to a saved quality report in JSON format on Dapla.
    """

    def __init__(
        self,
        get_edits_list_func: Callable[..., list[tuple[str, str]]],
        quality_report: QualityReport | None = None,
        qualityreport_path: str | None = None,
    ) -> None:
        """Initializes the accuracy indicator view for the quality indicator modal.

        Args:
            get_edits_list_func (Callable):
                Function to fetch the list of edits made to the data. The list must contain tuples, which contain the identification variable of the observation that has been changed and the variable that was changed.
            quality_report (QualityReport | None):
                Quality report for calculations.
            qualityreport_path (str | None):
                File path to a saved quality report in JSON format.

        Raises:
            ValueError: If both `quality_report` and `qualityreport_path` are defined
                        or if neither is provided.
        """
        if qualityreport_path and quality_report:
            raise ValueError(
                "Remove either quality_report or qualityreport_path. QualityIndicatorTreffsikkerhet() requires that only one of quality_report and qualityreport_path is defined. If both are defined, it will not work."
            )
        if qualityreport_path:
            import json

            import dapla as dp

            with dp.FileClient.gcs_open(qualityreport_path, "r") as outfile:
                data = json.load(outfile)
            self.quality_report = data
        elif quality_report:
            self.quality_report = quality_report
        else:
            raise ValueError(
                "Either quality_report or qualityreport_path needs to have a value."
            )
        self.get_edits_list_func = get_edits_list_func

        self.treffsikkerhet = self.beregn_treffsikkerhet()

        self.card = html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.H5("26 - Treffsikkerhet", className="card-title"),
                                dcc.Graph(
                                    figure=go.Figure(
                                        go.Indicator(
                                            mode="number+delta",
                                            value=self.treffsikkerhet["total"],
                                            number={"prefix": ""},
                                            # delta={"position": "bottom", "reference": self.editeringsandel(self.periode-1)}, # TODO
                                            domain={"x": [0, 1], "y": [0, 1]},
                                        )
                                    ).update_layout(
                                        height=150,
                                        margin=dict(l=20, r=20, t=20, b=20),
                                    ),
                                    config={"displayModeBar": False},
                                ),
                            ]
                        ),
                        dbc.CardFooter(
                            dbc.Button(
                                "Detaljer",
                                id="kvalitet-treffsikkerhet-button-details",
                            )
                        ),
                    ],
                    style={
                        "width": "18rem",
                        "margin": "10px",
                    },
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader("26 - Treffsikkerhet"),
                        dbc.ModalBody(
                            [
                                html.Div(
                                    dcc.Graph(
                                        figure=px.bar(
                                            y=self.treffsikkerhet.keys(),
                                            x=self.treffsikkerhet.values(),
                                            orientation="h",
                                        )
                                    )
                                ),
                            ]
                        ),
                    ],
                    id="treffsikkerhet-modal",
                ),
            ]
        )

        self.callbacks()

    def beregn_treffsikkerhet(self) -> dict[str, float]:
        """Calculates the accuracy indicator based on the quality report.

        Returns:
            dict: A dictionary where keys are control names and values are the accuracy percentage.
                  Includes a "total" key for overall accuracy.
        """
        if isinstance(self.quality_report, QualityReport):
            quality_report = self.quality_report.to_dict()
        else:
            quality_report = self.quality_report
        edits = self.get_edits_list_func()
        treffsikkerhet = {}
        total_kontrollutslag = 0
        total_celler_markert_editert = 0
        for i in quality_report["control_documentation"]:
            kontrollutslag = quality_report["control_documentation"][i][
                "Kontrollutslag"
            ]
            total_kontrollutslag = total_kontrollutslag + kontrollutslag
            celler_markert = [
                (x["observasjon_id"], var)
                for x in quality_report["kontrollutslag"]
                if x["kontrollnavn"] == i
                for var in x["relevante_variabler"]
            ]
            celler_markert_editert = len([x for x in edits if x in celler_markert])
            total_celler_markert_editert = (
                total_celler_markert_editert + celler_markert_editert
            )
            treffsikkerhet[i] = (celler_markert_editert / kontrollutslag) * 100
        treffsikkerhet["total"] = (
            total_celler_markert_editert / total_kontrollutslag
        ) * 100
        return treffsikkerhet

    def callbacks(self) -> None:
        """Sets up callbacks for opening and closing the detailed view."""

        @callback(  # type: ignore[misc]
            Output("treffsikkerhet-modal", "is_open"),
            Input("kvalitet-treffsikkerhet-button-details", "n_clicks"),
            State("treffsikkerhet-modal", "is_open"),
        )
        def kvalitettreffsikkerhet_modaltoggle(n: int, is_open: bool) -> bool:
            """Toggles the modal displaying detailed accuracy information.

            Args:
                n (int): Number of clicks on the "Detaljer" button.
                is_open (bool): Current state of the modal.

            Returns:
                bool: New state of the modal (True for open, False for closed).
            """
            if n:
                return not is_open
            return is_open
