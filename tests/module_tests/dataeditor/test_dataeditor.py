import pandas as pd

import pytest


def test_dataeditor_python_api():
    from ssb_dash_framework import (
        DataEditor,
        DataEditorSupportTables,
        DataEditorSupportTable,
        DataEditorHistory,
        DataEditorSidebarEditingStatus,
        DataEditorSidebarComment,
        DataEditorTable,
        DataViewCustom,
        StandardDataHandler,
        EditorSettings,
        VariableSelectorConfig,
    )

    from ssb_dash_framework.utils.config_tools.set_variables import (
        TimeUnit,
        TimeUnitType,
    )

    VariableSelectorConfig(
        refnr="refnr",
        ident="ident",
        time_units=TimeUnit(name="iso_period", frequency=TimeUnitType.MONTH),
        grouping_variables=["altinnskjema", "variabel"],
    )

    empty_df = lambda: pd.DataFrame()

    example_layout = {}

    handler = StandardDataHandler()
    settings = EditorSettings(
        starting_table="skjemadata",
        form_data_table="skjemadata",
        form_list=["RA-0187"],
        period_col="iso_period",
        ident_col="ident",
        refnr_col="refnr",
        form_name_col="skjema",
        field_name_col="feltsti",
        field_value_col="verdi",
    )

    instance = DataEditor(
        settings=settings,
        data_handler=handler,
        inforow={
            "orgnr": {"source": "variableselector", "variable_name": "ident"},
            "navn": {"source": "enhetsinfo", "variable_name": "navn"},
            "skjema": {"source": "variableselector", "variable_name": "altinnskjema"},
        },
        buttons=[
            # DataEditorSupportTables(
            #     [
            #         DataEditorSupportTable(
            #             label="Empty table",
            #             inputs=["ident", "aar"],
            #             get_data_func=empty_df,
            #         )
            #     ]
            # ),
            DataEditorHistory(),
        ],
        sidebar=[
            DataEditorSidebarEditingStatus(),
            DataEditorSidebarComment(),
        ],
        dataview=[
            # DataEditorTable(
            #     applies_to_tables=["skjemadata"],
            #     applies_to_forms=["RA-xxxx"],
            # ),
            DataViewCustom(
                layout={"layout": {}},
            ),
        ],
    )

    assert instance is not None
    assert isinstance(instance, DataEditor)


def test_dataeditor_yaml_based():
    from ssb_dash_framework import DataEditor

    instance = DataEditor.from_yaml("dataeditor_test.yaml")

    assert instance is not None
    assert isinstance(instance, DataEditor)
