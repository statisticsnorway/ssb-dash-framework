"""Contains base classes for DataEditor functionality and some utilities."""

import logging
from abc import ABC
from abc import abstractmethod
from typing import Any

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
from ibis import _

from ssb_dash_framework import VariableSelector
from ssb_dash_framework.utils.config_tools.set_variables import get_ident
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units
from ssb_dash_framework.utils.core_query_functions import create_filter_dict
from ssb_dash_framework.utils.core_query_functions import ibis_filter_with_dict

from ....utils.config_tools.connection import get_connection
from .registry import DataEditorRegistry

logger = logging.getLogger(__name__)


class DataEditor:
    """A module designed as a modular catch-all for micro-focused tasks.

    Intended to be tailored to specific needs, the module is almost a mini-framework within the framework.

    It has a few different types of components that can be added to it.

    DataViews are to view data on a micro level, and can be tailored to have a specific view of specific parts of the data.

    Sidebar components are components added to the sidebar on the left side of the module.
    These add functionality or contextual information about what the dataview is showing.

    Helper buttons add functionality by adding a button that opens / activates the functionality in a row above the data view.

    Info row provide a way to show some key information about the specific unit / form that is currently selected.
    """

    _id_number = 0

    def __init__(
        self,
        enable_table_selector: bool = True,
        starting_table: str = "skjemadata_hoved",
        table_list: list[str] | None = None,
    ) -> None:
        """Initializes the DataEditor module.

        Args:
            enable_table_selector: Decides if the DataEditorTableSelector component should be activated or not, strongly recommended to leave it enabled.
            starting_table: Sets the default value of the DataEditorTableSelector dropdown.
            table_list: A list of tables that will show up in the dropdown menu.
                Defaults to None, which will try to find all tables with the 'skjemadata_' prefix.

        Raises:
            NotImplementedError: if another instance of DataEditor is already running. Current implementation does not support multiple of the DataEditor module.

        Note:
            This module needs to be initialized last, as components need to already be registered in order to be collected.
        """
        if DataEditor._id_number != 0:
            raise NotImplementedError(
                "Currently DataEditor can only be initialized once in your layout.\nMultiple of the module cannot exist in the same app."
            )
        self.module_number = DataEditor._id_number
        self.module_name = self.__class__.__name__
        DataEditor._id_number += 1

        if enable_table_selector:
            self.enable_table_selector = True
            DataEditorTableSelector(
                starting_table=starting_table, table_list=table_list
            )
        else:
            self.enable_table_selector = False
            logger.warning(
                "Without a table selector, it will not be possible to choose which table to view.\nDataEditor looks for the selected table as the 'value' attribute from the id 'dataeditortableselector'."
            )

        self.icon = "🗊"
        self.label = "Data editor"

        self.gather_components()
        self.module_callbacks()

    def gather_components(self) -> None:
        """Using the DataEditorRegistry, this method assembles the DataEditor module with currently enabled components."""
        logger.debug(
            f"Gathering components based on current DataEditorRegistry:\n{DataEditorRegistry()}"
        )
        self.info_view = html.Div(
            [module.layout() for module in DataEditorRegistry.info_fields],
            className="dataeditor-info-view",
        )
        self.helper_row = dbc.Row(
            [dbc.Col(module.layout()) for module in DataEditorRegistry.helper_modules]
        )
        self.sidebar = html.Div(
            [
                dbc.Card(dbc.CardBody(module.layout()))
                for module in DataEditorRegistry.sidebar_modules
            ]
        )
        _existing_views = []
        main_views = []

        self.make_default_view()

        for divname, info in DataEditorRegistry.main_views.items():
            logger.debug(
                f"Adding '{divname}' to main_views. Applies to:\ntables: '{info['tables']}'\nforms: {info['forms']}"
            )
            try:
                if divname not in _existing_views:
                    main_views.append(info["instance"].layout())
                    _existing_views.append(divname)
                    logger.debug(f"Added '{divname}' to main_views.")
                else:
                    logger.debug(
                        f"Not adding {divname} due to it already existing. Existing views: {_existing_views}"
                    )
            except Exception as e:
                logger.error(
                    f"Encountered error '{e}' when adding main_view '{divname}' with configuration:\n{info}",
                    exc_info=True,
                )
                raise e
        self.main_view = html.Div(
            id=f"{self.module_name}-{self.module_number}-div",
            children=[view for view in main_views],
        )

    def make_default_view(self) -> None:
        """Creates a default view for table-form pairs without a specific one to prevent blank screen."""
        with get_connection() as conn:
            t = conn.table("skjemamottak")
            t = t.select("skjema").distinct().execute()

            with_view = set(DataEditorRegistry._table_form_covered)

            undefined_view: dict[str, list[str]] = {}
            for table in [
                table for table in conn.list_tables() if table.startswith("skjemadata_")
            ]:
                for form in t["skjema"].unique():
                    if (table, form) not in with_view:
                        undefined_view.setdefault(table, []).append(form)

        try:
            from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_table import (
                DataEditorTable,
            )

            for table in undefined_view:
                DataEditorTable(
                    applies_to_tables=[table], applies_to_forms=undefined_view[table]
                )
        except Exception as e:
            logger.error("Error during creation of default view.", exc_info=True)
            raise e

    def _create_layout(self) -> dbc.Container:
        """Creates the layout for the DataEditor module."""
        return dbc.Container(
            [
                dbc.Row(html.H1(id=f"{self.module_name}-{self.module_number}-header")),
                dbc.Row(self.info_view),
                dbc.Row(
                    [
                        dbc.Col(self.sidebar, width=2),
                        dbc.Col(
                            [
                                dbc.Row(dbc.Card(dbc.CardBody(self.helper_row))),
                                dbc.Row(dbc.Card(dbc.CardBody(self.main_view))),
                            ],
                            width=10,
                        ),
                    ]
                ),
            ],
            fluid=True,
        )

    def layout(self) -> dbc.Container:
        """Generates the layout for the DataEditor."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Registers the callbacks for the DataEditor."""

        @callback(
            *[
                Output(main_view, "style")
                for main_view in DataEditorRegistry.main_views
            ],
            Input("dataeditortableselector", "value"),
            VariableSelector([], []).get_input("altinnskjema"),
        )
        def update_main_view(
            selected_table: str, selected_form: str
        ) -> dict[str, Any] | list[dict[str, Any]]:
            """Checks which table and form is currently selected and shows the appropriate view.

            Unused views are set to be hidden, but still exists in the layout.
            """
            logger.debug(f"Selected table: {selected_table}")
            styles: list[dict[str, Any]] = []
            for divname in DataEditorRegistry.main_views:
                if (
                    selected_table in DataEditorRegistry.main_views[divname]["tables"]
                    and selected_form in DataEditorRegistry.main_views[divname]["forms"]
                ):
                    styles.append({"display": "block"})
                else:
                    styles.append({"display": "none"})
            if all(style == {"display": "none"} for style in styles):
                message = f"No main_view defined for {selected_table} - {selected_form}"
                logger.error(message)
                raise ValueError(message)
            if len(DataEditorRegistry.main_views) == 1:
                logger.debug(
                    "Returning a single dict due to only one main_view being defined"
                )
                return styles[
                    0
                ]  # Dash expects a single value when there is just one output.
            else:
                return styles

        @callback(
            Output(f"{self.module_name}-{self.module_number}-header", "children"),
            Input("dataeditortableselector", "value"),
            VariableSelector([], []).get_input("altinnskjema"),
        )
        def update_header(
            selected_table: str, selected_form: str
        ) -> str:  # TODO: make prettier
            """Show an info message telling the user which form and table are currently selected."""
            return f"Viser data for {selected_form} fra tabell {selected_table}"


class DataEditorTableSelector:
    """Default module to select datasource table to show data for."""

    _id_number = 0

    def __init__(
        self,
        starting_table: str = "skjemadata_hoved",
        table_list: list[str] | None = None,
    ) -> None:
        """Initializes the table selector component.

        Args:
            starting_table: Sets the default value of the DataEditorTableSelector dropdown.
            table_list: Optional override to default list of tables. Defaults to getting all tables starting with the prefix 'skjemadata_'.

        Raises:
            NotImplementedError: if another instance of DataEditorTableSelector is already running. Current implementation does not support multiple of the DataEditorTableSelector module.
            ValueError: If starting table does not exist in table_list.
        """
        if DataEditorTableSelector._id_number != 0:
            raise NotImplementedError(
                "Currently DataEditorTableSelector can only be initialized once in your layout.\nMultiple of the module cannot exist in the same app."
            )
        self.module_number = DataEditorTableSelector._id_number
        self.module_name = self.__class__.__name__
        DataEditorTableSelector._id_number += 1
        if not table_list:
            with get_connection() as conn:
                table_list = [
                    table
                    for table in conn.list_tables()
                    if table.startswith("skjemadata_")
                ]
        self.table_options = [{"label": item, "value": item} for item in table_list]

        if starting_table not in table_list:
            raise ValueError(
                f"Selected starting table not found in data source.\nExpected one of: '{table_list}'.\nReceived: '{starting_table}'"
            )
        self.starting_table = starting_table

        DataEditorRegistry.sidebar_modules.insert(0, self)

    def _create_layout(self) -> html.Div:
        """Creates the component."""
        return html.Div(
            [
                dbc.Label("Tabellvelger"),
                dcc.Dropdown(
                    id="dataeditortableselector",
                    options=self.table_options,
                    value=self.starting_table,
                ),
            ]
        )

    def layout(self) -> html.Div:
        """Returns the layout containing the component."""
        return self._create_layout()

    def module_callbacks(
        self,
    ) -> None:  # TODO Add a way to connect selected table to variable selector?
        """Registers callbacks. Currently no callbacks required from the module itself."""
        pass


from pydantic import BaseModel


class InfoRowField(BaseModel):
    """Model for a info field in the DataEditorInfoRow module."""

    name: str
    source: str
    source_variable_name: str


class DataEditorInfoRow:
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

        DataEditorRegistry.info_fields.append(self)

    def _create_layout(self) -> dbc.Row:
        info_fields = []
        for info_var in self.info_variables:
            info_fields.append(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            id=f"info-var-label-{info_var}", children=info_var
                        ),
                        dbc.CardBody(id=f"info-var-field-{info_var}"),
                    ]
                )
            )

        return dbc.Row(dbc.CardGroup(info_fields))

    def layout(self) -> dbc.Row:
        """Returns the module layout."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Registers callbacks for the module."""
        variableselector = VariableSelector(
            selected_inputs=[],
            selected_states=[
                self.info_variables[x]["variable_name"]
                for x in self.info_variables
                if self.info_variables[x]["source"] == "variableselector"
            ],
        )

        @callback(
            [
                Output(f"info-var-field-{info_var}", "children")
                for info_var in self.info_variables
            ],
            variableselector.get_input(get_ident()),
            *[variableselector.get_input(unit) for unit in get_time_units().keys()],
            *[variableselector.get_all_states()],
        )
        def get_data_for_info_row_fields(
            ident: str, *args: Any
        ) -> list[str | int | float | bool | None]:
            logger.debug(f"ident: {ident}\nargs: {args}")
            info_values = []
            time_unit_list = [x for x in get_time_units().keys()]
            time_units = args[: len(time_unit_list)]
            collected_states = 0
            states = args[len(time_unit_list) :]
            filter_dict = create_filter_dict(time_unit_list, time_units)
            with get_connection(necessary_tables=["enhetsinfo"]) as conn:
                for info_var in self.info_variables:
                    logger.debug(f"{info_var}\n{self.info_variables[info_var]}")
                    if self.info_variables[info_var]["source"] == "variableselector":
                        value = states[collected_states]
                        collected_states += 1
                    else:
                        t = conn.table(self.info_variables[info_var]["source"])
                        t = t.filter(_.ident == ident).filter(
                            ibis_filter_with_dict(filter_dict)
                        )
                        data = t.filter(
                            _.variabel == self.info_variables[info_var]["variable_name"]
                        ).to_pandas()
                        logger.debug(data)
                        value = data["verdi"].item()
                    info_values.append(value)
                    logger.debug("info_values: ", info_values)

            return info_values


class DataEditorHelperButton:
    """Base class for defining a helper button component."""

    _id_number = 0

    def __init__(self, label: str) -> None:
        """Core functionality to register the component and make the button functional.

        After being initialized it registers itself to DataEditorRegistry.

        Args:
            label: The label to put on the button.
        """
        self.label = label
        self.button_callbacks()
        DataEditorRegistry.helper_modules.append(self)

    def layout(self) -> html.Div:
        """Returns the layout of the module."""
        if not hasattr(self, "modal_body"):
            raise AttributeError("Lacking 'modal_body' attribute.")
        return html.Div(
            [
                dbc.Button(
                    self.label, id=f"{self.module_name}-{self.module_number}-button"
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle(self.label)),
                        dbc.ModalBody(self.modal_body),
                    ],
                    id=f"{self.module_name}-{self.module_number}-modal",
                    is_open=False,
                    className="dataeditor-helper-button-modal",
                ),
            ]
        )

    def button_callbacks(self) -> None:
        """Registers the callbacks for the DataEditor Support Tables module."""

        @callback(  # type: ignore[misc]
            Output(f"{self.module_name}-{self.module_number}-modal", "is_open"),
            Input(f"{self.module_name}-{self.module_number}-button", "n_clicks"),
            State(f"{self.module_name}-{self.module_number}-modal", "is_open"),
        )
        def toggle_hjelpetabellmodal(n_clicks: None | int, is_open: bool) -> bool:
            logger.debug(f"Args:\nn_clicks: {n_clicks}\nis_open: {is_open}")
            if n_clicks is None:
                logger.debug("Raised PreventUpdate")
                raise PreventUpdate
            if not is_open:
                return True
            return False


class DataEditorHelperSidebar(ABC):
    """Base class for defining a helper sidebar component."""

    def __init__(self) -> None:
        """Registers the component to the DataEditorRegistry."""
        DataEditorRegistry.sidebar_modules.append(self)

    @abstractmethod
    def _create_layout(self) -> html.Div:
        """Creates the layout for the module."""
        pass

    def layout(self) -> html.Div:
        """Returns the layout of the module."""
        return self._create_layout()

    @abstractmethod
    def module_callbacks(self) -> None:
        """Registers callbacks for the module."""
        pass


class DataEditorDataView(ABC):
    """Base class for defining a data view."""

    def __init__(
        self, applies_to_tables: str | list[str], applies_to_forms: str | list[str]
    ) -> None:
        """Initializes and registers a DataEditorDataView module.

        Args:
            applies_to_tables: A list of tables in the database that this view should apply to.
            applies_to_forms: A list of forms that this view should apply to.¨

        Raises:
            TypeError: If not all tables and forms in applies_to_tables and applies_to_forms are strings.
        """
        if isinstance(applies_to_tables, str):
            applies_to_tables = [applies_to_tables]
        self.applies_to_tables = applies_to_tables
        if isinstance(applies_to_forms, str):
            applies_to_forms = [applies_to_forms]
        self.applies_to_forms = applies_to_forms

        DataEditorRegistry.main_views.update(
            {
                self.divname: {
                    "tables": self.applies_to_tables,
                    "forms": self.applies_to_forms,
                    "name": self.module_name,
                    "number": self.module_number,
                    "instance": self,
                }
            }
        )
        for table in self.applies_to_tables:
            if not isinstance(table, str):
                raise TypeError(
                    f"Expected all tables to be strings. Received: '{table}' of type '{type(table)}'"
                )
            for form in self.applies_to_forms:
                if not isinstance(form, str):
                    raise TypeError(
                        f"Expected all forms to be strings. Received: '{form}' of type '{type(form)}'"
                    )
                DataEditorRegistry._table_form_covered.append((table, form))

    @abstractmethod
    def _create_layout(self) -> None:
        """Abstract method for creating the module layout."""
        pass

    def layout(self) -> None:
        """Returns the module layout."""
        return self._create_layout()

    @abstractmethod
    def module_callbacks(self) -> None:
        """Abstract method to register callbacks."""
        pass
