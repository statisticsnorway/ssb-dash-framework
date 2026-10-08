import json

import pandas as pd


# @pytest.mark.skip(reason="Work in progress")
def test_dataeditor_python_api():
    from ssb_dash_framework import DataEditor
    from ssb_dash_framework import DataEditorContactInfo
    from ssb_dash_framework import DataEditorHistory
    from ssb_dash_framework import DataEditorSidebarComment
    from ssb_dash_framework import DataEditorSidebarEditingStatus
    from ssb_dash_framework import DataViewCustom
    from ssb_dash_framework import EditorSettings
    from ssb_dash_framework import StandardDataHandler
    from ssb_dash_framework import VariableSelectorConfig
    from ssb_dash_framework.setup.variableselector.time_unit import TimeUnit
    from ssb_dash_framework.setup.variableselector.time_unit import TimeUnitType

    DataEditor.module_number = 0  # Reset the count

    VariableSelectorConfig(
        refnr="refnr",
        ident="ident",
        time_units=TimeUnit(name="iso_period", frequency=TimeUnitType.MONTH),
        grouping_variables=["altinnskjema", "variabel"],
    )

    empty_df = lambda: pd.DataFrame()

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
            DataEditorContactInfo(),
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
                layout=[{"type": "row", "children": []}],
            ),
        ],
    )

    assert instance is not None
    assert isinstance(instance, DataEditor)


# @pytest.mark.skip(reason="Work in progress")
def test_dataeditor_yaml_based():
    from ssb_dash_framework import AppConfig
    from ssb_dash_framework import DataEditor
    from ssb_dash_framework import build_app_from_config
    from ssb_dash_framework import config_parser_yaml

    DataEditor.module_number = 0  # Reset the count

    path = "tests/unittests/module_tests/dataeditor/dataeditor_test.yaml"
    if path.endswith(".yaml"):
        yaml_content = config_parser_yaml(path)

    print(json.dumps(yaml_content, indent=2))

    config = AppConfig(**yaml_content)
    app, tabs, windows = build_app_from_config(config)
    instance = tabs[0]

    assert instance is not None
    assert isinstance(instance, DataEditor)


# @pytest.mark.skip(reason="Work in progress")
def test_dataeditor_yaml_settings_override():
    """Test to assert that overriding EditorSettings variable in the microlayout yaml-definition works"""
    from ssb_dash_framework import DataEditor
    from ssb_dash_framework import DataViewCustom
    from ssb_dash_framework import EditorSettings
    from ssb_dash_framework import StandardDataHandler
    from ssb_dash_framework import VariableSelector

    VariableSelector.get_refnr = lambda x: x  # pyright: ignore
    original = EditorSettings.model_validate

    @classmethod
    def custom_validate(cls, *args, **kwargs):
        data = args[0]
        if data["form_data_table"] == "ny":
            assert data["field_name_col"] == "feltstier"
            assert data["field_value_col"] == "verdier"
        else:
            assert data["field_name_col"] == "feltsti"
            assert data["field_value_col"] == "verdi"
        return original(*args, **kwargs)

    EditorSettings.model_validate = custom_validate  # pyright: ignore
    DataEditor.module_number = 0  # Reset the count

    path = "tests/unittests/module_tests/dataeditor/override.yaml"
    instance = DataViewCustom.from_yaml_path(path)
    instance.fetcher = StandardDataHandler()
    instance.instance_id = "None"
    instance.settings = EditorSettings(
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
    layout = instance.layout()
    assert layout is not None
