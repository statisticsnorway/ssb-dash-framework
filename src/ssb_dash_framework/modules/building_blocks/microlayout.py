import logging
import uuid
from collections.abc import Callable

from dash import Input
from dash import State
from dash import html

from ibis import _
from .microlayout_components.editable_field_model import CallbackSettings
from .microlayout_components.models import Layout
logger = logging.getLogger(__name__)

class MicroLayoutAIO(html.Div):
    """A class for generating a dash layout and callbacks without interacting with Dash.

    The class uses a predefined layout for creating a static html layout and generating callbacks so the user doesn't have to.
    The user is expected to supply a function for getting data from the backend and a function to update data on the backend.
    """

    def __init__(
        self,
        layout: list[dict] | Layout,
        getter_func: Callable[..., tuple],
        update_func: Callable[..., tuple | None],
        form_reference_input_id: str,
        inputs: list[Input] | None = None,
        states: list[State] | None = None,
        getter_args: None | list = None,
        aio_id: str | None = None,
        horizontal: bool = False,
        form_data_table: str = "skjemadata",
        form_reference_number_column: str = "refnr",
        form_data_field_name_column: str = "feltnavn",
        formdata_field_value_column_name: str = "verdi",
    ) -> None:
        logger.warning(
            "This module is under development and might receive larger and/or breaking changes."
        )
        self.aio_id = aio_id or str(uuid.uuid4())
        if isinstance(layout, Layout):
            model = layout
        else:
            model = Layout(layout)

        if getter_args:
            extra_args = getter_args
        else:
            extra_args = []
        common_settings = CallbackSettings(
            form_data_table=form_data_table,
            form_reference_input_id=form_reference_input_id,
            form_reference_number_column=form_reference_number_column,
            formdata_fieldname_column=form_data_field_name_column,
            formdata_field_value_column_name=formdata_field_value_column_name,
        )
        html_layout = model.build(
            settings=common_settings,
            inputs=inputs,
            states=states,
            getter_args=extra_args
        )
        styles = {}

        if horizontal:
            styles["display"] = "flex"

        super().__init__(html_layout, id=f"{self.aio_id}-klass", style=styles)

