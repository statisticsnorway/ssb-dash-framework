import pandas as pd

import pytest

@pytest.mark.skip(reason="Work in progress")
def test_dataeditor_python_api():
    from ssb_dash_framework import DataEditor, DataEditorSupportTables, DataEditorSupportTable, DataEditorHistory, DataEditorSidebarEditingStatus, DataEditorSidebarComment, DataEditorTable, DataViewCustom

    empty_df = lambda: pd.DataFrame()

    example_layout = []

    instance = DataEditor(
        inforow = {
            "orgnr": {"source": "variableselector", "variable_name": "ident"},
            "navn": {"source": "enhetsinfo", "variable_name": "navn"},
            "skjema": {"source": "variableselector", "variable_name": "altinnskjema"},
        },
        buttons = [
            DataEditorSupportTables(
                [
                    DataEditorSupportTable(
                        label="Empty table",
                        inputs=["ident", "aar"],
                        get_data_func=empty_df,
                    )
                ]
            ),
            DataEditorHistory()
        ],
        sidebar = [
            DataEditorSidebarEditingStatus(),
            DataEditorSidebarComment(),
        ],
        dataview = [
            DataEditorTable(
                applies_to_tables=["skjemadata"],
                applies_to_forms=["RA-xxxx"],
            ),
            DataViewCustom(
                applies_to_tables=["skjemadata"],
                applies_to_forms=["RA-yyyy"],
                layout=example_layout,
            )
        ]
    )

    assert instance is not None
    assert type(instance, DataEditor)

@pytest.mark.skip(reason="Work in progress")
def test_dataeditor_yaml_based():
    from ssb_dash_framework import DataEditor
    instance = DataEditor.from_yaml("dataeditor_test.yaml")

    assert instance is not None
    assert type(instance, DataEditor)