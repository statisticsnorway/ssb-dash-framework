import logging
import uuid
from collections.abc import Callable

from dash import Input
from dash import State
from dash import html

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
        table_selector_id: str | None = None,
        form_selector_id: str | None = None,
        applies_to_tables: str | list[str] | None = None,
        applies_to_forms: str | list[str] | None = None,
    ) -> None:
        logger.warning(
            "This module is under development and might receive larger and/or breaking changes."
        )
        # The below is just for the __str__ dunder
        self._form_data_table = form_data_table
        self._form_reference_number_column = form_reference_number_column
        self._form_data_field_name_column = form_data_field_name_column
        self._formdata_field_value_column_name = formdata_field_value_column_name
        self._form_reference_input_id = form_reference_input_id
        self._table_selector_id = table_selector_id
        self._form_selector_id = form_selector_id
        self._applies_to_tables = applies_to_tables
        self._applies_to_forms = applies_to_forms
        self._horizontal = horizontal
        self._getter_func = getter_func
        self._update_func = update_func
        self._getter_args = getter_args
        # The above is just for the __str__ dunder

        self.aio_id = aio_id or str(uuid.uuid4())
        if isinstance(layout, Layout):
            model = layout
        else:
            model = Layout(layout)
        self._model = model  # Just for __str__ dunder

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
            table_selector_id=table_selector_id,
            form_selector_id=form_selector_id,
        )
        html_layout = model.build(
            settings=common_settings,
            inputs=inputs,
            states=states,
            getter_args=extra_args,
        )
        styles = {}

        if horizontal:
            styles["display"] = "flex"

        super().__init__(html_layout, id=f"{self.aio_id}-klass", style=styles)

    def __str__(self) -> str:
        lines = [
            self.__class__.__name__,
            f"  aio_id:               {self.aio_id}",
            f"  form_data_table:      {self._form_data_table}",
            f"  form_reference_col:   {self._form_reference_number_column}",
            f"  field_name_col:       {self._form_data_field_name_column}",
            f"  field_value_col:      {self._formdata_field_value_column_name}",
            f"  form_reference_id:    {self._form_reference_input_id}",
            f"  table_selector_id:    {self._table_selector_id}",
            f"  form_selector_id:     {self._form_selector_id}",
            f"  applies_to_tables:    {self._applies_to_tables}",
            f"  applies_to_forms:     {self._applies_to_forms}",
            f"  horizontal:           {self._horizontal}",
            f"  getter_func:          {self._getter_func.__name__}",
            f"  update_func:          {self._update_func.__name__}",
            f"  getter_args:          {self._getter_args}",
            "",
            str(self._model),
        ]
        return "\n".join(lines)
