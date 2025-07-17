import json

import plotly.express as px
from dapla import FileClient
from dash import Input
from dash import Output
from dash import callback
from dash import dcc
from dash import html

from ..setup.variableselector import VariableSelector
from ..utils import TabImplementation
from ..utils import WindowImplementation
from ..utils.module_validation import module_validator


class MapDisplay:
    _id_number = 0

    def __init__(
        self, map_type: str, aar_var, inputs, states, get_data_func, label=None
    ) -> None:
        self.module_number = MapDisplay._id_number
        self.module_name = self.__class__.__name__
        MapDisplay._id_number += 1
        self.icon = "📚"
        self.label = label if label else f"Kart {map_type}"
        if aar_var in inputs or aar_var in states:
            raise ValueError(
                "inputs or states cannot contain the same value as aar_var. {aar_var} will be used as input, so you do not need to add it as a separate input or state."
            )
        if map_type not in ["komm_nr", "fylke_nr"]:
            raise ValueError("Unsupported map type.")
        self.map_type = map_type

        self.get_data_func = get_data_func
        print([aar_var, *inputs])
        self.variableselector = VariableSelector(
            selected_inputs=[aar_var, *inputs], selected_states=states
        )
        self.is_valid()
        self.module_layout = self._create_layout()
        self.module_callbacks()
        module_validator(self)

    def is_valid(self):
        try:
            VariableSelector([], []).get_option(self.map_type)
        except ValueError as e:
            raise ValueError(
                f"Needs to have '{self.map_type}' defined as option"
            ) from e

    def get_data(self, *args):
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

    def get_geojson(self, year):  # TODO use year from variableselector
        if self.map_type == "komm_nr":
            self.geojson = fs = FileClient.get_gcs_file_system()
            with fs.open(
                f"gs://ssb-areal-data-delt-kart-prod/visualisering_data/klargjorte-data/{year}/geojson/N5000_kommune_flate_4326_p{year}.geojson",
                "r",
            ) as f:
                self.geojson = json.load(f)

    def create_map_figure(self, year):
        self.get_geojson(year)
        px.choropleth_mapbox(
            self.data,
            geojson=self.geojson,
            color="verdi",
            locations=self.data[self.map_type],
            featureidkey=f"properties.{self.map_type}",
            mapbox_style="carto-positron",
            center={"lat": 63.5, "lon": 10.5},
        )

    def _create_layout(self):
        return html.Div(dcc.Graph(id="map-figure"))

    def module_callbacks(self):
        dynamic_states = [
            self.variableselector.get_inputs(),
            self.variableselector.get_states(),
        ]
        @callback(
            Output("map-figure", "Figure"),
            *dynamic_states
        )
        def update_map(*args):
            print(f"update_map args: {args}")
            self.get_data(args)
            return self.create_map_figure(year=args[0])

        @callback(
            self.variableselector.get_output_object(self.map_type),
            Input("map-figure", "clickdata"),
            prevent_initial_call = True
        )
        def click_to_varselector(clickdata):
            print(clickdata)
            return clickdata


class MapDisplayTab(TabImplementation, MapDisplay):
    """MapDisplay implemented as a Tab."""

    def __init__(self, map_type: str, aar_var, inputs, states, get_data_func) -> None:
        """Initialize the MapDisplayTab.

        Args:
            label (str): The label for the MapDisplayTab.
            module_list (list[Any]): A list of modules to switch between. Each module should have
        """
        MapDisplay.__init__(
            self,
            map_type,
            aar_var=aar_var,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
        )
        TabImplementation.__init__(
            self,
        )


class MapDisplayWindow(WindowImplementation, MapDisplay):
    """MapDisplay implemented as a Window."""

    def __init__(self, map_type: str, aar_var, inputs, states, get_data_func) -> None:
        """Initialize the MapDisplayWindow.

        Args:
            label (str): The label for the MapDisplayWindow.
            module_list (list[Any]): A list of modules to switch between. Each module should have
        """
        MapDisplay.__init__(
            self,
            map_type,
            aar_var=aar_var,
            inputs=inputs,
            states=states,
            get_data_func=get_data_func,
        )
        WindowImplementation.__init__(self)
