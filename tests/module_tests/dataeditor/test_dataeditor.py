import pytest

from ssb_dash_framework import StandardDataHandler
from ssb_dash_framework.modules.data_editor import FetcherMeta


def test_standard_data_handler_inheritance():
    handler = StandardDataHandler()
    assert isinstance(handler, FetcherMeta)


PERIOD = "2026"
IDENT = "ATF2134660"
REFNR = "f7d1ca75eddd"
VARIABLE = "prefillAreal"


@pytest.mark.backends("sqlite", "postgres", "parquedit")
def test_standard_data_handler_getters():
    handler = StandardDataHandler()
    handler.get_field()
    handler.get_comment(refnr=REFNR)
    handler.get_history(refnr=REFNR, insert_toggle=True)
    handler.get_contact_info(refnr=REFNR)
    handler.get_form_status(refnr=REFNR)
    handler.get_refnrs_by_period_ident(period=PERIOD, ident=IDENT)
    handler.get_info_row_fields(refnr=REFNR, period=PERIOD)
    handler.get_timeseries(
        variable=VARIABLE, refnr=REFNR, ident=IDENT, periods=[PERIOD]
    )
    handler.get_dynamic_list()


@pytest.mark.backends("postgres")
def test_standard_data_handler_updates_postgres():
    handler = StandardDataHandler()

    new_value = "Updated"
    handler.update_field_value(value=new_value)
    assert handler.get_field() == new_value

    new_value = "Ferdig"
    handler.update_form_status(status_code=new_value)
    assert handler.get_form_status() == new_value

    new_value = False
    handler.update_form_active_status(value=new_value)
    assert handler.get_form_active_status() == new_value

    new_value = "New comment"
    handler.update_form_reception_comment(comment=new_value)
    assert handler.get_form_reception_comment() == new_value


@pytest.mark.backends("parquedit")
def test_standard_data_handler_updates_parquedit():
    handler = StandardDataHandler()

    new_value = "Updated"
    handler.update_field_value(value=new_value)
    assert handler.get_field() == new_value

    new_value = "Ferdig"
    handler.update_form_status(status_code=new_value)
    assert handler.get_form_status() == new_value

    new_value = False
    handler.update_form_active_status(value=new_value)
    assert handler.get_form_active_status() == new_value

    new_value = "New comment"
    handler.update_form_reception_comment(comment=new_value)
    assert handler.get_form_reception_comment() == new_value
