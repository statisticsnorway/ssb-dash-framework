
from pydantic import ValidationError

from ssb_poc_statlog_model.change_data_log import ChangeDataLog
from ssb_dash_framework import ParquetEditor, set_variables


def test_changelog_creation() -> None:
    set_variables(["aar", "orgnr"])
    example_change = {
        'rowIndex': 0, 'rowId': '0', 'data':
    {'aar': 2024, 'orgnr': '971526920', 'ansatte': 100, 'inntekter': 230, 'utgifter': 99},
    'oldValue': 90, 'value': 100, 'colId': 'ansatte', 'timestamp': 1764140468399} | {"reason": "REVIEW", "comment": ""}

    test = ParquetEditor(
        statistics_name="Test",
        id_vars=["aar","orgnr"],
        data_source="/inndata/dummypath.parquet",
        data_target = "/klargjorte-data/dummypath.parquet"
    )
    changelog = test._build_process_log_entry(example_change)

    ChangeDataLog.model_validate(changelog)
