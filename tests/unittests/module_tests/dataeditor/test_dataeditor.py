from typing import cast

import pytest

from ssb_dash_framework import EditorSettings
from ssb_dash_framework import StandardDataHandler
from ssb_dash_framework import _get_connection_object
from ssb_dash_framework.modules.data_editor import FetcherMeta
from ssb_dash_framework.modules.data_editor.default_getter.form_tools_parquedit_handler import (
    AltinnFormParqueditHandler,
)
from ssb_dash_framework.modules.data_editor.modules.microlayout.microlayout_components.editable_field_model import (
    EditableField,
)
from ssb_dash_framework.modules.data_editor.modules.microlayout.microlayout_components.editable_field_model import (
    FieldCallbackContainer,
)


def test_standard_data_handler_inheritance():
    handler = StandardDataHandler()
    assert isinstance(handler, FetcherMeta)


PERIOD = "2024"
IDENT = "ATF2134660"
REFNR = "f7d1ca75eddd"
VARIABLE = "prefillAreal"
FELTSTI = "/prefillAreal"
SKJEMA = "RA-0745"
VERDI = "61"
COMMENT = "kommentar"

CONTACT_PERSON = "DOLLY DUCK"
CONTACT_PHONE = "12345678"


@pytest.mark.backends("sqlite", "postgres", "parquedit")
def test_standard_data_handler_getters(subtests: pytest.Subtests):
    editor_settings = EditorSettings(
        starting_table="skjemadata",
        form_data_table="skjemadata",
        form_list=[SKJEMA],
        period_col="iso_period",
        ident_col="ident",
        refnr_col="refnr",
        form_name_col="skjema",
        field_name_col="feltsti",
        field_value_col="verdi",
    )
    settings: EditableField = EditableField(variable=FELTSTI, id="", type="")
    callback_settings = FieldCallbackContainer(settings=settings, parent_id="")

    handler = StandardDataHandler()
    with subtests.test(property="get_field"):
        field_value = handler.get_field(
            editor_settings, callback_settings, [REFNR, PERIOD]
        )
        assert field_value == VERDI
    with subtests.test(property="get_comment"):
        comment = handler.get_comment(refnr=REFNR)
        assert comment == COMMENT

    with subtests.test(property="get_contact_info"):
        contact_info = handler.get_contact_info(refnr=REFNR)
        assert contact_info.kontaktperson == CONTACT_PERSON
        assert contact_info.telefon == CONTACT_PHONE

    with subtests.test(property="get_form_status"):
        form_status = handler.get_form_status(refnr=REFNR)
        assert form_status is not None
        assert form_status.aktiv == True
        assert form_status.status == "Ubehandlet"

    with subtests.test(property="get_refnrs_by_period_ident"):
        refnumbers = handler.get_refnrs_by_period_ident(
            editor_settings, period=PERIOD, ident=IDENT
        )
        assert len(refnumbers) == 1
        assert refnumbers[0].kommentar == COMMENT

    with subtests.test(property="get_info_row_fields"):
        row_field = handler.get_info_row_fields(
            settings=editor_settings,
            refnr=IDENT,
            period=PERIOD,
            fields=[
                InfoRowField(
                    name="enhetsPostnr",
                    source="enhetsinfo",
                    source_variable_name="enhetsPostnr",
                )
            ],
            states={},
        )
        assert row_field is not None
        assert len(row_field) == 1
        assert row_field["enhetsPostnr"] == "2350"

    with subtests.test(property="get_timeseries"):
        timeseries = handler.get_timeseries(
            settings=editor_settings,
            variable=FELTSTI,
            refnr=REFNR,
            ident=IDENT,
            periods=["2026", "2025", "2024"],
        )
        timeseries.sort(key=lambda x: x["iso_period"])
        assert len(timeseries) == len(
            [
                {"iso_period": "2024", "/prefillAreal": "61"},
                {"iso_period": "2025", "/prefillAreal": "64"},
                {"iso_period": "2026", "/prefillAreal": "67"},
            ]
        )

    with subtests.test(property="get_dynamic_list"):
        result = handler.get_dynamic_list(
            editor_settings, "/NyEngSpredUtsGroup/%/%", REFNR
        )

        expected_result = [
            {
                "feltsti_parent": "/NyEngSpredUtsGroup/0",
                "NyEngSpredUtsGjodsMengde": "31",
                "NyEngSpredUtsID": "00",
                "NyEngSpredUtsNavn": "Bredspreder for bløtgjødsel med tankvogn",
            },
            {
                "feltsti_parent": "/NyEngSpredUtsGroup/11",
                "NyEngSpredUtsGjodsMengde": "132",
                "NyEngSpredUtsID": "TOTAL_ROW",
                "NyEngSpredUtsNavn": "Husdyrgjødsel spredd totalt",
            },
            {
                "feltsti_parent": "/NyEngSpredUtsGroup/9",
                "NyEngSpredUtsGjodsMengde": "101",
                "NyEngSpredUtsID": "09",
                "NyEngSpredUtsNavn": "Gjødselvogn med spredevalser for fastgjødsel",
            },
        ]
        result.sort(key=lambda x: x["feltsti_parent"])
        assert result == expected_result


"""
@pytest.mark.backends("sqlite")
def test_standard_data_handler_updates_postgres(subtests: pytest.Subtests):
    handler = StandardDataHandler()

    editor_settings = EditorSettings(
        starting_table="skjemadata",
        form_data_table="skjemadata",
        form_list=[SKJEMA],
        period_col="iso_period",
        ident_col="ident",
        refnr_col="refnr",
        form_name_col="skjema",
        field_name_col="feltsti",
        field_value_col="verdi",
    )
    settings: EditableField = EditableField(variable=FELTSTI, id="", type="")
    callback_settings = FieldCallbackContainer(settings=settings, parent_id="")

    #new_value = "Updated"
    #handler.update_field_value(value=new_value)
    #assert handler.get_field() == new_value
    with subtests.test(property="update_field_value"):
        new_value = "Updated"

        handler.update_field_value(
            refnr=REFNR,
            ident=IDENT,
            period=PERIOD,
            value=new_value,
            old_value="61",
            skjema=SKJEMA,
            settings=editor_settings,
            container=callback_settings,
            inputs=[],
            editing_code="OTHER",
        )
        handler.cache.evict(REFNR, "skjemadata")

        assert (
            handler.get_field(editor_settings, callback_settings, [REFNR, PERIOD])
            == new_value
        )
        handler.update_field_value(
            refnr=REFNR,
            ident=IDENT,
            period=PERIOD,
            value=new_value,
            old_value="61",
            skjema=SKJEMA,
            settings=editor_settings,
            container=callback_settings,
            inputs=[],
            editing_code="OTHER",
        )
        handler.cache.evict(REFNR, "skjemadata")

    #new_value = "Ferdig"
    #handler.update_form_status(status_code=new_value)
    #assert handler.get_form_status() == new_value

    #new_value = False
    #handler.update_form_active_status(value=new_value)
    #assert handler.get_form_active_status() == new_value

    #new_value = "New comment"
    #handler.update_form_reception_comment(comment=new_value)
    #assert handler.get_form_reception_comment() == new_value
"""


@pytest.mark.backends("parquedit")
def test_standard_data_handler_updates_parquedit(subtests: pytest.Subtests):
    from ssb_parquedit import ParquEdit

    conn = cast(ParquEdit, _get_connection_object())
    handler = AltinnFormParqueditHandler(conn)

    editor_settings = EditorSettings(
        starting_table="skjemadata",
        form_data_table="skjemadata",
        form_list=[SKJEMA],
        period_col="iso_period",
        ident_col="ident",
        refnr_col="refnr",
        form_name_col="skjema",
        field_name_col="feltsti",
        field_value_col="verdi",
    )
    settings: EditableField = EditableField(variable=FELTSTI, id="", type="")
    callback_settings = FieldCallbackContainer(settings=settings, parent_id="")

    with subtests.test(property="update_field_value"):
        new_value = "Updated"

        handler.update_field_value(
            refnr=REFNR,
            ident=IDENT,
            period=PERIOD,
            value=new_value,
            old_value="61",
            skjema=SKJEMA,
            settings=editor_settings,
            container=callback_settings,
            inputs=[],
            editing_code="OTHER",
        )
        handler.cache.evict(REFNR, "skjemadata")

        assert (
            handler.get_field(editor_settings, callback_settings, [REFNR, PERIOD])
            == new_value
        )
        handler.update_field_value(
            refnr=REFNR,
            ident=IDENT,
            period=PERIOD,
            value=new_value,
            old_value="61",
            skjema=SKJEMA,
            settings=editor_settings,
            container=callback_settings,
            inputs=[],
            editing_code="OTHER",
        )
        handler.cache.evict(REFNR, "skjemadata")

    with subtests.test(property="update_form_status"):
        new_value = "Ferdig"
        handler.cache.evict(REFNR, "skjemamottak")
        handler.update_form_status(REFNR, status_code=new_value)
        new_val = (
            conn._get_connection()
            .raw.execute(f"SELECT * FROM skjemamottak WHERE refnr = '{REFNR}'")
            .fetch_df()["status"]
            .iloc[0]
        )
        assert new_val is not None
        assert new_val == new_value

    with subtests.test(property="update_form_active_status"):
        new_value = False
        handler.update_form_active_status(REFNR, value=new_value)
        new_val = handler.get_form_status(REFNR)
        assert new_val is not None
        assert new_val.aktiv == new_value

    with subtests.test(property="update_form_reception_comment"):
        new_value = "New comment"
        handler.update_form_reception_comment(REFNR, comment=new_value)
        assert handler.get_comment(REFNR) == new_value

    with subtests.test(property="get_history"):
        history = handler.get_history(refnr=REFNR, insert_toogle=True)
        assert len(history) == 2
