import logging

import eimerdb as db
import os
import glob
from pathlib import Path
import logging
import time
import pickle
from datetime import datetime
from sklearn.model_selection import train_test_split
import pandas as pd
import eimerdb as db
from statstruk import ratemodel
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import callback
from dash import dcc
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from ..utils.alert_handler import create_alert
from ..utils.functions import sidebar_button

logger = logging.getLogger(__name__)

class RateModelModule:
    def __init__(self, id_var, cache_location, get_sample_func, get_population_func):
        self.id_var = id_var
        self.cache_location = cache_location
        self.get_sample_func = get_sample_func
        self.get_population_func = get_population_func
        self.callbacks()


    def get_model(self, x_var, y_var, strata_var, force_rerun=False):
        start = time.time()
        logger.info("Getting model")
        cache_path = Path(f"{self.cache_location}/ratemodel_{x_var}_{y_var}_{strata_var}.pickle")
        if cache_path.is_file() and not force_rerun:
            logger.info("Retrieving model from cache")
            model_dict = get_cached_model(cache_path)
        else:
            logger.info("No cache found, getting data and calculating model")
            sampledata = self.get_sample_func()
            popdata = self.get_population_func()
            logger.info("Calculating model")
            mod = ratemodel(popdata, sampledata, id_nr=self.id_var)
            mod.fit(x_var=x_var, y_var=y_var, strata_var=strata_var)
            model_dict = save_cache_model(cache_path, mod)
        end = time.time()
        logger.info(f"Done getting model in {end-start}")
        return model_dict

    def get_cached_model(path):
        with open(path, 'rb') as handle:
            return pickle.load(handle)
        return None


    def save_cache_model(self, path, model):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d-%H-%M")
        for_cache = {
            "model": model,
            "compute_time": timestamp
        }
        with open(path, 'wb') as handle:
            pickle.dump(for_cache, handle, protocol=pickle.HIGHEST_PROTOCOL)
        return for_cache


    def clear_cache(self):
        logger.info("Clearing cached ratemodels")
        files_to_remove = glob.glob(os.path.join(self.cache_location, 'ratemodel_*.pickle'))
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f'Removed: {file_path}')
            except Exception as e:
                print(f'Error removing {file_path}: {e}')

    def layout(self):
        layout_extreme = html.Div(
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle()),
                    dbc.ModalBody(
                        [
                            dag.AgGrid(id = "ratemodel_detailtable_extreme")
                        ]
                    )
                ],
                id = "ratemodel_detailmodal_extreme"
            )
        )

        layout_imputation = html.Div(
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle()),
                    dbc.ModalBody(
                        [
                            dag.AgGrid(id="ratemodel_detailtable_imputation")
                        ]
                    )
                ],
                id = "ratemodel_detailmodal_imputation"
            )
        )

        layout_weights = html.Div(
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle()),
                    dbc.ModalBody(
                        [
                            dag.AgGrid(id="ratemodel_detailtable_weights")
                        ]
                    )
                ],
                id = "ratemodel_detailmodal_weights"
            )
        )
        
        layout = html.Div(
            [
                layout_extreme,
                layout_imputation,
                layout_weights,
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Ratemodell")),
                        dbc.ModalBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(dcc.Dropdown(id="ratemodel_xvar", value="fulldyrket",options = [{"label":"fulldyrket", "value": "fulldyrket"}])),
                                        dbc.Col(dcc.Dropdown(id="ratemodel_yvar", value = "arealtilskudd", options = [{"label":"arealtilskudd", "value": "arealtilskudd"}])),
                                        dbc.Col(dcc.Dropdown(id = "ratemodel_strata", value="fylke", options = [{"label":"fylke", "value": "fylke"}])),
                                        dbc.Col(dbc.Button("Hent modell", id = "ratemodel_button_run"))
                                    ]
                                ),
                                dcc.Loading([
                                    dbc.Row( # Info about the model returned
                                        [
                                            dbc.Col(id="ratemodel_timestamp"),
                                            dbc.Col(dbc.Button("Beregn ny modell", id = "ratemodel_button_rerun")),
                                            dbc.Col(dbc.Button("Slett alle cached modeller", id = "ratemodel_button_clear_cache"))
                                        ]
                                    ),
                                    dbc.Row(),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Row(html.P("Estimater")),
                                                    dbc.Row(dag.AgGrid(id="ratemodel_estimates"))
                                                ]
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Row(html.P("Usikkerhetsmål")),
                                                    dbc.Row(
                                                        dcc.Dropdown(
                                                            id="ratemodel_uncertainty",
                                                            options = [
                                                                {"label": "CV", "value": "CV"},
                                                                {"label": "", "value": ""},
                                                                {"label": "", "value": ""},
                                                                {"label": "", "value": ""},
                                                                {"label": "", "value": ""}
                                                            ]
                                                        )
                                                    ),
                                                    dbc.Row(html.P("Varianstype")),
                                                    dbc.Row(
                                                        dcc.Dropdown(
                                                            id="ratemodel_variance",
                                                            options = [
                                                                {"label": "Standard", "value": "standard"},
                                                                {"label": "Robust", "value": "robust"}
                                                            ]
                                                        )
                                                    ),
                                                    dbc.Row(dbc.Button("Ekstremverdier", id="ratemodel_detailbutton_extreme")),
                                                    dbc.Row(dbc.Button("Imputerte verdier", id="ratemodel_detailbutton_imputation")),
                                                    dbc.Row(dbc.Button("Vekter", id="ratemodel_detailbutton_weights"))
                                                ]
                                            )
                                        ]
                                    )
                                ])
                                
                            ]
                        )
                    ],
                    id="ratemodel-modal",
                    size="xl",
                    fullscreen="xxl-down",
                ),
                sidebar_button("🔎", "Ratemodell", "sidebar-ratemodel-button"),
            ]
        )
        return layout

    def callbacks(self):
        @callback(  # type: ignore[misc]
            Output("alert_store", "data", allow_duplicate=True),
            Input("ratemodel_button_clear_cache", "n_clicks"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def ratemodel_clear_cache(n_clicks, error_log):
            self.clear_cache()
            return [create_alert(
                        "Cache for modeller er slettet",
                        "info",
                        ephemeral=True,
                ), *error_log]
        
        @callback(  # type: ignore[misc]
            Output("ratemodel-modal", "is_open"),
            Input("sidebar-ratemodel-button", "n_clicks"),
            State("ratemodel-modal", "is_open"),
        )
        def ratemodel_toggle(n: int, is_open: bool) -> bool:
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
            Output("ratemodel_detailmodal_extreme", "is_open"),
            Input("ratemodel_detailbutton_extreme", "n_clicks"),
            State("ratemodel_detailmodal_extreme", "is_open"),
        )
        def ratemodel_extreme_toggle(n: int, is_open: bool) -> bool:
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
            Output("ratemodel_detailmodal_imputation", "is_open"),
            Input("ratemodel_detailbutton_imputation", "n_clicks"),
            State("ratemodel_detailmodal_imputation", "is_open"),
        )
        def ratemodel_extreme_toggle(n: int, is_open: bool) -> bool:
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
            Output("ratemodel_detailmodal_weights", "is_open"),
            Input("ratemodel_detailbutton_weights", "n_clicks"),
            State("ratemodel_detailmodal_weights", "is_open"),
        )
        def ratemodel_extreme_toggle(n: int, is_open: bool) -> bool:
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

        @callback(
            Output("alert_store", "data", allow_duplicate=True),
            Output("ratemodel_timestamp", "children"),
            Output("ratemodel_estimates", "rowData"),
            Output("ratemodel_estimates", "columnDefs"),
            Output("ratemodel_detailtable_extreme", "rowData"),
            Output("ratemodel_detailtable_extreme", "columnDefs"),
            Output("ratemodel_detailtable_imputation", "rowData"),
            Output("ratemodel_detailtable_imputation", "columnDefs"),
            Output("ratemodel_detailtable_weights", "rowData"),
            Output("ratemodel_detailtable_weights", "columnDefs"),
            Input("ratemodel_button_run", "n_clicks"),
            Input("ratemodel_button_rerun", "n_clicks"),
            Input("ratemodel_uncertainty", "value"),
            Input("ratemodel_variance", "value"),
            State("ratemodel_xvar", "value"),
            State("ratemodel_yvar", "value"),
            State("ratemodel_strata", "value"),
            State("alert_store", "data"),
            prevent_initial_call=True,
        )
        def ratemodel_run_model(click, more_important_click, uncertainty, variance, x_var, y_var, strata_var, error_log):
            logger.info(f"Model requested for {x_var} - {y_var} - {strata_var}")
            model_dict = self.get_model(x_var = x_var, y_var = y_var, strata_var = strata_var)
            model_timestamp = model_dict["compute_time"]
            model = model_dict["model"]
            estimates = model.get_estimates(uncertainty_type = uncertainty, variance_type = variance)
            extremes = model.get_extremes()
            imputation = model.get_imputed()
            weigths = model.get_weights()

            error_log = [create_alert(
                        f"Modell kjørt for {x_var} - {y_var} - {strata_var}",
                        "info",
                        ephemeral=True,
                ), *error_log]
            
            return error_log, f"Modell ble beregnet {model_timestamp}", estimates.to_dict("records"), [{"field": col} for col in estimates.columns], extremes.to_dict("records"), [{"field": col} for col in extremes.columns], imputation.to_dict("records"), [{"field": col} for col in imputation.columns], weigths.to_dict("records"), [{"field": col} for col in weigths.columns]