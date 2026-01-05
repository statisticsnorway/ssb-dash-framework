import os

from ssb_poc_statlog_model.change_data_log import ChangeDataLog

from ssb_dash_framework import ParquetEditor
from ssb_dash_framework import set_variables


def test_changelog_creation() -> None:
    os.environ["DAPLA_USER"] = "TEST"
    set_variables(["aar", "orgnr"])
    example_change = {
        "rowIndex": 0,
        "rowId": "0",
        "data": {
            "orgnr": "971526920",
            "aar": 2024,
            "ansatte": 150,
            "inntekter": None,
            "utgifter": 200,
        },
        "oldValue": 140,
        "value": 150,
        "colId": "ansatte",
        "timestamp": 1764168184878,
        "reason": "REVIEW",
        "comment": "Tester",
    }  # reason and comment are user generated, the rest come directly from AgGrid

    test = ParquetEditor(
        statistics_name="Test",
        id_vars=["aar", "orgnr"],
        data_source="/buckets/eksempelstatistikk/inndata/dummypath.parquet",
    )
    changelog = test._build_process_log_entry(example_change)

    ChangeDataLog.model_validate(changelog)
