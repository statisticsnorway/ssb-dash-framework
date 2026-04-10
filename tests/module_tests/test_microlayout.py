import pytest
from dash import html

from ssb_dash_framework import MicroLayoutAIO


def test_import_freesearch() -> None:
    assert MicroLayoutAIO is not None, "MicroLayoutAIO is not importable"


def test_instantiation(ibis_polars_conn) -> None:
    component = MicroLayoutAIO(
        form_reference_input_id="var-refnr",
        layout=[],
        getter_func=lambda x: (x,),
        update_func=lambda x: (x,),
        inputs=[],
        states=[],
    )
    assert issubclass(MicroLayoutAIO, html.Div)
    assert isinstance(component, MicroLayoutAIO)


# Vibe coded tests:


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def callback_settings():
    from ssb_dash_framework.modules.building_blocks.microlayout_components.editable_field_model import (
        CallbackSettings,
    )

    return CallbackSettings(
        form_data_table="skjemadata",
        form_reference_input_id="refnr",
        form_reference_number_column="refnr",
        formdata_field_value_column_name="verdi",
        formdata_fieldname_column="feltnavn",
    )


# ---------------------------------------------------------------------------
# EditableField
# ---------------------------------------------------------------------------


def test_editable_field_defaults():
    from ssb_dash_framework.modules.building_blocks.microlayout_components.editable_field_model import (
        EditableField,
    )
    from ssb_dash_framework.modules.building_blocks.microlayout_components.editable_field_model import (
        default_updater,
    )
    from ssb_dash_framework.modules.building_blocks.microlayout_components.editable_field_model import (
        defult_getter,
    )

    field = EditableField(field_path="my_field")
    assert field.field_path == "my_field"
    assert field.getter_func is defult_getter
    assert field.update_func is default_updater
    assert field.applies_to_tables == []
    assert field.applies_to_forms == []


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def test_header_node():
    from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
        Header,
    )

    node = Header(type="header", label="My Header")
    assert node.label == "My Header"
    assert node.size == "md"


def test_input_node():
    from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
        InputField,
    )

    node = InputField(
        type="input", label="My Input", field_settings={"field_path": "my_var"}
    )
    assert node.label == "My Input"
    assert node.field_settings.field_path == "my_var"


def test_col_node():
    from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
        Col,
    )

    node = Col(type="col", children=[{"type": "header", "label": "Hi"}])
    assert len(node.children) == 1
    assert node.children[0].type == "header"


def test_row_node():
    from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
        Row,
    )

    node = Row(type="row", children=[{"type": "col", "children": []}])
    assert len(node.children) == 1
    assert node.children[0].type == "col"


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def test_layout_parses_and_builds(callback_settings):
    from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
        Layout,
    )

    layout = Layout(
        [
            {"type": "header", "label": "Title"},
            {
                "type": "col",
                "children": [
                    {
                        "type": "input",
                        "label": "Field",
                        "field_settings": {"field_path": "my_var"},
                    }
                ],
            },
        ]
    )
    assert len(layout.nodes) == 2
    components = layout.build(settings=callback_settings)
    assert len(components) == 2


def test_layout_str():
    from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
        Layout,
    )

    layout = Layout([{"type": "header", "label": "Title"}])
    result = str(layout)
    assert "LAYOUT:" in result
    assert "HEADER" in result
