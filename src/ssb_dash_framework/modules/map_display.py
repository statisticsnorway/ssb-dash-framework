import logging
from collections.abc import Callable
from typing import Any
from typing import ClassVar

import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input
from dash import Output
from dash import callback
from dash import dcc
from dash import html

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator

logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)


class MapDisplay:
    """Module used for creating a map visualization.

    When supplied with a get_data_func that returns data grouped by a valid geography it creates a map figure with coloring showing the column 'value' on different geographical units.

    Note:
        You need read access to the bucket "areal-data-delt-kart-prod" in order to use this module as this is where it finds the shapefiles.
    """

    _id_number: ClassVar[int] = 0
    supported_map_types: ClassVar[list[str]] = ["komm_nr", "fylke_nr"]

    def __init__(
        self,
        map_type: str,
        aar_var: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        clickdata_func: Callable[..., Any] | None = None,
        output_var: str | None = None,
        label: str | None = None,
    ) -> None:
        """Initialize the MapDisplay module.

        Args:
            map_type(str): The kind of map to be made, currently supports komm_nr and fylke_nr.
            aar_var (str): The name of your year variable in the variable selector.
            inputs (list[str]): List the variables from the variable selector that should trigger an update to the map
            states (list[str]): List the variables from the variable selector that should be used in the get_data_func, but not trigger an update to the map
            get_data_func (Callable[..., Any]): Function that when given aar_var, *inputs and *states as arguments returns a dataframe with a column with the same name as the map type and 'value' for the value.
            clickdata_func (Callable[..., Any] | None, optional): A function to process the click data.
                It should accept the click data as an argument and return a value to be sent to the output variable.
                If None, no click data will be processed. Defaults to None.
            output_var (str): Variable selector output for clickdata. Defaults to the same value as map_type.
            label (str): Label for the button / tab for the module. Defaults to 'Kart {map_type}'

        Raises:
            ValueError: If supplied unsupported map_type.

        Note:
            - The clickdata_func needs to process the click data and return a string value that will be sent to the output variable specified in the output argument.
            - clickdata is a dictionary with the structure:
                {
                    "points": [
                        {
                        "curveNumber": 1,
                        "pointNumber": 0,
                        "pointIndex": 0,
                        "x": 1,
                        "y": 3,
                        "bbox": {
                            "x0": 189.35,
                            "x1": 209.35,
                            "y0": 1057.72,
                            "y1": 1077.72
                        },
                        "customdata": [
                            3
                        ]
                        }
                    ]
                }
        """
        self.module_number = MapDisplay._id_number
        self.module_name = self.__class__.__name__
        MapDisplay._id_number += 1
        self.icon = "🗺️"
        self.label = label if label else f"Kart {map_type}"
        if aar_var in inputs or aar_var in states:
            raise ValueError(
                f"inputs or states cannot contain the same value as aar_var. {aar_var} will be used as input, so you do not need to add it as a separate input or state."
            )
        if map_type not in MapDisplay.supported_map_types:
            raise ValueError("Unsupported map type.")
        self.map_type = map_type

        self.get_data_func = get_data_func
        self.clickdata_func = clickdata_func
        self.output_var = output_var
        self.variableselector = VariableSelector(
            selected_inputs=[aar_var, *inputs], selected_states=states
        )
        self.is_valid()
        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)

    def is_valid(self) -> None:
        """Does some validation checks for the module."""
        try:
            VariableSelector([], []).get_option(self.map_type)
        except ValueError as e:
            raise ValueError(
                f"Needs to have '{self.map_type}' defined as option"
            ) from e

    def get_data(self, *args: Any) -> None:
        """Gets data for the map figure by using get_data_func."""
        self.data = self.get_data_func(*args)
        if self.map_type == "komm_nr":
            required_columns = {"komm_nr", "value"}
        elif self.map_type == "fylke_nr":
            required_columns = {"fylke_nr", "value"}
        else:
            raise ValueError("Map type is invalid.")
        missing = required_columns - set(self.data.columns)
        if missing:
            raise ValueError(f"Missing required columns in DataFrame: {missing}")
        self.data = self.geoshape.merge(self.data).to_crs(4326).set_index(self.map_type)

    def get_geoshape(self, year: str) -> None:
        """Gets the parquet file with geometry from the shared bucket."""
        if self.map_type == "komm_nr":
            self.geoshape = gpd.read_parquet(
                f"gs://ssb-areal-data-delt-kart-prod/visualisering_data/klargjorte-data/{year}/parquet/N5000_kommune_flate_p{year}.parquet"
            )

    def create_map_figure(self) -> go.Figure:
        """Creates the map figure."""
        fig = px.choropleth_mapbox(
            geojson=self.data["geometry"],
            locations=self.data.index,
            color=self.data["value"],
            center={"lat": 59.9138, "lon": 10.7387},
            mapbox_style="open-street-map",
            zoom=4,
        ).update_traces(marker_line_width=0)
        fig.write_html("Kart.html")
        logger.debug("Returning map figure")
        return fig

    def _create_layout(self) -> html.Div:
        """Creates the layout for the module."""
        return html.Div(
            dcc.Graph(
                id="map-figure",
                className="figuredisplay-graph",
            ),
            className="figuredisplay",
        )

    def module_callbacks(self) -> None:
        """Registers module callbacks."""
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]

        @callback(Output("map-figure", "figure"), *dynamic_states)  # type: ignore[misc]
        def update_map(*args: Any) -> go.Figure:
            print(f"update_map args: {args}")
            self.get_geoshape(year=args[0])
            self.get_data(*args)
            logger.debug("Creating map figure")
            return self.create_map_figure()

        if self.clickdata_func and self.output_var:
            output_var = self.output_var or self.map_type
            logger.debug(f"Connecting clickdata callback to {output_var}.")

            @callback(  # type: ignore[misc]
                self.variableselector.get_output_object(output_var),
                Input("map-figure", "clickData"),
                prevent_initial_call=True,
            )
            def click_to_varselector(
                clickdata: dict[str, list[dict[str, str | int | float | bool]]],
            ) -> str:
                logger.debug(clickdata)
                if self.clickdata_func is None:
                    logger.warning(
                        "No clickdata_func provided, click data will not be processed."
                    )
                    return "No clickdata_func provided"
                return str(self.clickdata_func(clickdata))

        else:
            logger.debug(
                "No clickdata connection defined, will not create callback for it."
            )


class MapDisplayTab(TabImplementation, MapDisplay):
    """MapDisplay implemented as a Tab."""

    def __init__(
        self,
        map_type: str,
        aar_var: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        clickdata_func: Callable[..., Any] | None = None,
        output_var: str | None = None,
        label: str | None = None,
    ) -> None:
        """Initialize the MapDisplayTab module.

        Args:
            map_type(str): The kind of map to be made, currently supports komm_nr and fylke_nr.
            aar_var (str): The name of your year variable in the variable selector.
            inputs (list[str]): List the variables from the variable selector that should trigger an update to the map
            states (list[str]): List the variables from the variable selector that should be used in the get_data_func, but not trigger an update to the map
            get_data_func (Callable[..., Any]): Function that when given aar_var, *inputs and *states as arguments returns a dataframe with a column with the same name as the map type and 'value' for the value.
            clickdata_func (Callable[..., Any] | None, optional): A function to process the click data.
                It should accept the click data as an argument and return a value to be sent to the output variable.
                If None, no click data will be processed. Defaults to None.
            output_var (str): Variable selector output for clickdata. Defaults to the same value as map_type.
            label (str): Label for the button / tab for the module. Defaults to 'Kart {map_type}'

        Note:
            - The clickdata_func needs to process the click data and return a string value that will be sent to the output variable specified in the output argument.
            - clickdata is a dictionary with the structure:
                {
                    "points": [
                        {
                        "curveNumber": 1,
                        "pointNumber": 0,
                        "pointIndex": 0,
                        "x": 1,
                        "y": 3,
                        "bbox": {
                            "x0": 189.35,
                            "x1": 209.35,
                            "y0": 1057.72,
                            "y1": 1077.72
                        },
                        "customdata": [
                            3
                        ]
                        }
                    ]
                }
        """
        MapDisplay.__init__(
            self,
            map_type,
            aar_var=aar_var,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
            clickdata_func=clickdata_func,
            output_var=output_var,
            label=label,
        )
        TabImplementation.__init__(
            self,
        )


class MapDisplayWindow(WindowImplementation, MapDisplay):
    """MapDisplay implemented as a Window."""

    def __init__(
        self,
        map_type: str,
        aar_var: str,
        inputs: list[str],
        states: list[str],
        get_data_func: Callable[..., Any],
        clickdata_func: Callable[..., Any] | None = None,
        output_var: str | None = None,
        label: str | None = None,
    ) -> None:
        """Initialize the MapDisplayWindow module.

        Args:
            map_type(str): The kind of map to be made, currently supports komm_nr and fylke_nr.
            aar_var (str): The name of your year variable in the variable selector.
            inputs (list[str]): List the variables from the variable selector that should trigger an update to the map
            states (list[str]): List the variables from the variable selector that should be used in the get_data_func, but not trigger an update to the map
            get_data_func (Callable[..., Any]): Function that when given aar_var, *inputs and *states as arguments returns a dataframe with a column with the same name as the map type and 'value' for the value.
            clickdata_func (Callable[..., Any] | None, optional): A function to process the click data.
                It should accept the click data as an argument and return a value to be sent to the output variable.
                If None, no click data will be processed. Defaults to None.
            output_var (str): Variable selector output for clickdata. Defaults to the same value as map_type.
            label (str): Label for the button / tab for the module. Defaults to 'Kart {map_type}'

        Note:
            - The clickdata_func needs to process the click data and return a string value that will be sent to the output variable specified in the output argument.
            - clickdata is a dictionary with the structure:
                {
                    "points": [
                        {
                        "curveNumber": 1,
                        "pointNumber": 0,
                        "pointIndex": 0,
                        "x": 1,
                        "y": 3,
                        "bbox": {
                            "x0": 189.35,
                            "x1": 209.35,
                            "y0": 1057.72,
                            "y1": 1077.72
                        },
                        "customdata": [
                            3
                        ]
                        }
                    ]
                }
        """
        MapDisplay.__init__(
            self,
            map_type,
            aar_var=aar_var,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
            clickdata_func=clickdata_func,
            output_var=output_var,
            label=label,
        )
        WindowImplementation.__init__(self)
