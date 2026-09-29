import logging
import uuid
from typing import Any
import time

from dash import Input
from dash import State
from dash import Output
from dash import callback
from dash import ctx
from dash import html
from dash import ALL
from dash import dcc
from dash.exceptions import PreventUpdate

from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework.utils.alert_handler import AlertHandler

from .meta import MicrolayoutMeta
from ...utils import EditorSettings
from ...utils import EDITING_CODE_DROPDOWN
from dash import no_update
from .microlayout_components.models import Layout
# from ssb_dash_framework.utils.core_models import FieldUpdateError

logger = logging.getLogger(__name__)


class FieldUpdateError(Exception):
    """Base class for failed field updates. The user has already been alerted."""

class InvalidValueError(FieldUpdateError):
    """The value was rejected by validation. Nothing was written."""

class UpdateFailedError(FieldUpdateError):
    """The database write failed."""


class MicroLayoutAIO(html.Div):
    """A class for generating a dash layout and callbacks without interacting with Dash.

    The class uses a predefined layout for creating a static html layout and generating callbacks so the user doesn't have to.
    The user is expected to supply a function for getting data from the backend and a function to update data on the backend.
    """

    def __init__(
        self,
        layout: list[dict] | dict | Layout,
        settings: EditorSettings,
        data_handler: MicrolayoutMeta,
        instance_id: str | None,
        inputs: list[Input] | dict[Any, Input] | None = None,
        states: list[State] | None = None,
        aio_id: str | None = None,
        horizontal: bool = False,
    ) -> None:
        logger.warning(
            "This module is under development and might receive larger and/or breaking changes."
        )

        if isinstance(layout, dict):
            override_kwargs = {}
            for key in [
                "form_data_table",
                "field_name_col",
                "refnr_col",
                "ident_col",
                "field_value_col",
                "period_col",
            ]:
                if key in layout:
                    override_kwargs[key] = layout[key]

            if override_kwargs:
                settings = settings.model_copy(update=override_kwargs)

        # The below is just for the __str__ dunder
        self.settings = settings
        self._horizontal = horizontal
        inputs = [] if inputs is None else inputs
        # The above is just for the __str__ dunder
        self.aio_id = aio_id or str(uuid.uuid4())
        if isinstance(layout, Layout):
            model = layout
        elif isinstance(layout, dict):
            model = Layout(layout["layout"], self.aio_id)
        else:
            model = Layout(layout, self.aio_id)
        self._model = model  # Just for __str__ dunder

        styles = {}

        if horizontal:
            styles["display"] = "flex"

        layout, ids = model.build(data_handler, settings)

        if layout is None:
            layout_children = []
        elif isinstance(layout, list):
            layout_children = list(layout)
        else:
            layout_children = [layout]

        local_store = dcc.Store(id={"type": "status-signal", "aio": self.aio_id})
        layout_children.append(local_store)

        super().__init__(
            layout_children, id=f"{self.aio_id}-klass", style=styles  # pyright: ignore
        )

        callback_ctx = {item._id: item for item in ids}

        def revert_upon_failed_edit(old_value):
            """Returns old value (prior to edit) to the frontend when an edit fails."""
            return {
                **{
                    id_: old_value if id_ == triggered_id else no_update
                    for id_ in all_ids
                },
                "status_signal": no_update,
            }
            
        if len(ids):

            @callback(
                output={
                    **{
                        item._id: Output(
                            {"comp_id": item._id, "aio": self.aio_id},
                            "value",
                        )
                        for item in ids
                    },
                    "status_signal": Output(
                        {"type": "status-signal", "aio": self.aio_id},
                        "data",
                    ),
                },
                inputs={
                    "fields": {item._id: item.get_input(self.aio_id) for item in ids},
                    "custom_inputs": inputs,
                    "refnr": VariableSelector.get_refnr(Input),
                    "skjema": VariableSelector.get_state("altinnskjema"),
                    "ident": VariableSelector.get_ident(State),
                    "period": VariableSelector.get_timevar(Input),
                    "editing_code": Input(
                        EDITING_CODE_DROPDOWN(instance_id), "value", allow_optional=True
                    ),
                },
                optional=True,
            )
            def handle_microlayout_callback(
                fields: dict[str, Any],
                custom_inputs: list | dict | None,
                refnr: str | None,
                skjema: str | None,
                ident: str | None,
                period: str | None,
                editing_code: str | None = None,
            ):
                all_ids = {item._id for item in ids}
                no_field_update = {id_: no_update for id_ in all_ids}

                is_edit = False
                if (
                    ctx.triggered_id
                    and isinstance(ctx.triggered_id, dict)
                    and ctx.triggered_id.get("aio") == self.aio_id
                ): # user edit or fetcher?
                    is_edit = True

                if (
                    ctx.triggered_id
                    and isinstance(ctx.triggered_id, str)
                    and ctx.triggered_id.endswith("-update-queue")
                ):
                    raise PreventUpdate

                if is_edit:
                    # edit & save logic
                    if not ident or not custom_inputs:
                        raise PreventUpdate

                    if isinstance(skjema, list):
                        skjema = skjema[0] if skjema else None
                    print(f"refnr: {refnr}")
                    print(f"ident: {ident}")
                    print(f"skjema: {skjema}")

                    triggered_id = ctx.triggered_id["comp_id"]
                    custom_ctx = callback_ctx.get(triggered_id)
                    value = fields.get(triggered_id)

                    if custom_ctx is None or value is None:
                        logger.debug(
                            "Skipping form value update since triggered id was none or it didn't match any fields"
                        )
                        raise PreventUpdate

                    old_value = None
                    try:
                        old_value = data_handler.get_field(
                            self.settings, custom_ctx, custom_inputs
                        )
                        logger.debug(f"Old value: {old_value}, new value: {value}")

                        if old_value == value:
                            logger.debug(
                                "Skipping form value update since value was same as previous value"
                            )
                            return {**no_field_update, "status_signal": no_update}

                        # set up to raise FieldUpdateError on failure
                        data_handler.update_field_value(
                            refnr,
                            skjema,
                            ident,
                            period=period,
                            value=value,
                            old_value=old_value,
                            settings=self.settings,
                            container=custom_ctx,
                            inputs=custom_inputs,
                            editing_code=editing_code,
                        )
                        status_signal = no_update
                        if self.settings.form_data_table.startswith("skjemadata"):
                            try:
                                changed = data_handler.update_form_status(  # sets status to "Under arbeid" only if it's currently "Ubehandlet"
                                    refnr, "Under arbeid", on_skjemadata_update=True
                                )
                                if changed:
                                    status_signal = time.time()
                            except Exception:
                                logger.warning(
                                    "Status bump failed after successful edit",
                                    exc_info=True,
                                )
                        return {**no_field_update, "status_signal": status_signal}

                    except PreventUpdate:
                        raise

                    except FieldUpdateError as e:
                        logger.info(
                            f"Field update rejected for {custom_ctx.settings.variable}: {e}"
                        )
                        return revert_upon_failed_edit(old_value)

                    except Exception as e:
                        logger.error(
                            f"Updating field {custom_ctx.settings.variable} failed unexpectedly: {e}",
                            exc_info=True,
                        )
                        AlertHandler.warning(
                            f"Uventet feil ved oppdatering av {custom_ctx.settings.variable}: {e}"
                        )
                        return revert_upon_failed_edit(old_value)
                else:
                    # fetcher/getter
                    if not custom_inputs:
                        raise PreventUpdate

                    field_values = {}
                    for id_, field in callback_ctx.items():
                        try:
                            field_val = data_handler.get_field(
                                self.settings, field, custom_inputs
                            )
                            field_values[id_] = field_val
                        except Exception as e:
                            msg = f"Getting data for form field {field} failed with error: {e}"
                            logger.warning(msg)
                            AlertHandler.warning(msg)
                            field_values[id_] = no_update

                    return {**field_values, "status_signal": no_update}


@callback(
    Output("skjemamottak-status-signal", "data", allow_duplicate=True),
    Input({"type": "status-signal", "aio": ALL}, "data"),
    prevent_initial_call=True,
)
def forward_status_signal(data_list):
    if not data_list:
        raise PreventUpdate
    valid_signals = [d for d in data_list if d is not None]
    if not valid_signals:
        raise PreventUpdate
    return valid_signals[-1]
