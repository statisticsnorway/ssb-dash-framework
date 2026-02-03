import json
import os
from pathlib import Path

import pandas as pd
import pytest
from ssb_poc_statlog_model.change_data_log import ChangeDataLog

from ssb_dash_framework import ParquetEditor
from ssb_dash_framework import export_from_parqueteditor
from ssb_dash_framework import get_export_log_path
from ssb_dash_framework import get_log_path
from ssb_dash_framework import set_variables


@pytest.fixture(autouse=True)
def disable_bucket_check(monkeypatch):
    monkeypatch.setattr(
        "ssb_dash_framework.modules.parquet_editor.check_for_bucket_path",
        lambda _: None,
    )


@pytest.fixture
def parquet_with_log(tmp_path):
    bucket_root = tmp_path / "buckets" / "testbucket"
    inndata_dir = bucket_root / "inndata"
    inndata_dir.mkdir(parents=True)

    # Source parquet
    data_source = inndata_dir / "source.parquet"
    df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 40, 80]})
    df.to_parquet(data_source)

    # Create matching process log
    log_path = get_log_path(str(data_source))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    processlog_entry = {
        "statistics_name": "TestStat",
        "data_source": [str(data_source)],
        "data_target": "data_target_placeholder",
        "data_period": "",
        "variable_name": "value",
        "change_event": "M",
        "change_event_reason": "REVIEW",
        "change_datetime": "2024-01-01T00:00:00Z",
        "changed_by": "tester",
        "data_change_type": "UPD",
        "change_comment": "test change",
        "change_details": {
            "detail_type": "unit",
            "unit_id": [{"unit_id_variable": "id", "unit_id_value": "1"}],
            "old_value": [{"variable_name": "value", "value": "10"}],
            "new_value": [{"variable_name": "value", "value": "20"}],
        },
    }

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(processlog_entry) + "\n")

    data_target = bucket_root / "utdata" / "exported.parquet"
    return str(data_source), str(data_target), bucket_root


def test_get_log_path():
    cases = {  # Key should be input, values should be expected output.
        "/buckets/produkt/editering-eksempel/inndata/test_p2024_v1.parquet": "/buckets/produkt/editering-eksempel/inndata/temp/parqueteditor/test_p2024_v1.jsonl",
        "/buckets/produkt/editering-eksempel/inndata/temp/test_p2024_v1.parquet": "/buckets/produkt/editering-eksempel/inndata/temp/parqueteditor/temp/test_p2024_v1.jsonl",
        "/buckets/produkt/editering-eksempel/klargjorte-data/temp/subfolder/another_subfolder/editeres_p2024_v1.parquet": "/buckets/produkt/editering-eksempel/klargjorte-data/temp/parqueteditor/temp/subfolder/another_subfolder/editeres_p2024_v1.jsonl",
        "/buckets/produkt/kirkekostra/klargjorte-data/temp/mindre/min-kirkefil_p2024_v1.parquet": "/buckets/produkt/kirkekostra/klargjorte-data/temp/parqueteditor/temp/mindre/min-kirkefil_p2024_v1.jsonl",
    }
    for given_input, expected in cases.items():
        assert str(get_log_path(given_input)) == expected


def test_get_export_log_path():
    cases = {  # Key should be input, values should be expected output.
        "/buckets/produkt/editering-eksempel/inndata/editert_p2024_v1.parquet": "/buckets/produkt/editering-eksempel/logg/produksjonslogg/inndata/editert_p2024_v1.jsonl",
        "/buckets/produkt/editering-eksempel/inndata/temp/subfolder/editert_p2024_v1.parquet": "/buckets/produkt/editering-eksempel/logg/produksjonslogg/inndata/temp/subfolder/editert_p2024_v1.jsonl",
        "/buckets/produkt/editering-eksempel/inndata/temp/subfolder/another_subfolder/editert_p2024_v1.parquet": "/buckets/produkt/editering-eksempel/logg/produksjonslogg/inndata/temp/subfolder/another_subfolder/editert_p2024_v1.jsonl",
        "/buckets/produkt/editering-eksempel/klargjorte-data/editert_p2024_v1.parquet": "/buckets/produkt/editering-eksempel/logg/produksjonslogg/klargjorte-data/editert_p2024_v1.jsonl",
        "/buckets/produkt/editering-eksempel/klargjorte-data/temp/subfolder/editert_p2024_v1.parquet": "/buckets/produkt/editering-eksempel/logg/produksjonslogg/klargjorte-data/temp/subfolder/editert_p2024_v1.jsonl",
        "/buckets/produkt/editering-eksempel/klargjorte-data/temp/subfolder/another_subfolder/editert_p2024_v1.parquet": "/buckets/produkt/editering-eksempel/logg/produksjonslogg/klargjorte-data/temp/subfolder/another_subfolder/editert_p2024_v1.jsonl",
        "/buckets/produkt/kirkekostra/klargjorte-data/temp/mindre/min-kirkefil_p2024_v1.parquet": "/buckets/produkt/kirkekostra/logg/produksjonslogg/klargjorte-data/temp/mindre/min-kirkefil_p2024_v1.jsonl",
    }
    for given_input, expected in cases.items():
        assert str(get_export_log_path(Path(given_input))) == expected


def test_changelog_creation_success(monkeypatch) -> None:
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

    import tempfile

    tmp_log_dir = tempfile.TemporaryDirectory()
    monkeypatch.setattr(
        "ssb_dash_framework.modules.parquet_editor.get_log_path",
        lambda path: Path(tmp_log_dir.name) / "dummy.jsonl",
    )

    test = ParquetEditor(
        statistics_name="Test",
        id_vars=["aar", "orgnr"],
        data_source="/buckets/eksempelstatistikk/inndata/dummypath.parquet",
    )

    changelog = test._build_process_log_entry(example_change)
    ChangeDataLog.model_validate(changelog)


def test_export_from_parqueteditor_success(parquet_with_log):
    data_source, data_target, _ = parquet_with_log

    export_from_parqueteditor(
        data_source=data_source,
        data_target=data_target,
        force_overwrite=False,
    )

    # ---- parquet exported ----
    assert Path(data_target).exists()
    exported_df = pd.read_parquet(data_target)
    assert exported_df.loc[0, "value"] == 20

    # ---- process log exported ----
    export_log_path = get_export_log_path(Path(data_target))
    assert export_log_path.exists()

    with open(export_log_path, encoding="utf-8") as f:
        lines = [json.loads(line) for line in f]
    assert lines[0]["data_target"] == data_target


def test_export_from_parqueteditor_missing_log(tmp_path):
    bucket_root = tmp_path / "buckets" / "testbucket"
    inndata_dir = bucket_root / "inndata"
    inndata_dir.mkdir(parents=True)

    data_source = inndata_dir / "source.parquet"
    pd.DataFrame({"id": [1], "value": [10]}).to_parquet(data_source)

    data_target = bucket_root / "utdata" / "exported.parquet"

    with pytest.raises(FileNotFoundError):
        export_from_parqueteditor(
            data_source=str(data_source),
            data_target=str(data_target),
        )


def test_export_from_parqueteditor_existing_target(parquet_with_log):
    data_source, data_target, _ = parquet_with_log

    # Create target beforehand
    Path(data_target).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"x": [1]}).to_parquet(data_target)

    with pytest.raises(FileExistsError):
        export_from_parqueteditor(
            data_source=data_source,
            data_target=data_target,
            force_overwrite=False,
        )


def test_export_from_parqueteditor_existing_processlog(parquet_with_log):
    data_source, data_target, _ = parquet_with_log

    # Pre-create exported process log
    export_log_path = get_export_log_path(Path(data_target))
    export_log_path.parent.mkdir(parents=True, exist_ok=True)
    export_log_path.write_text("existing log")

    with pytest.raises(FileExistsError):
        export_from_parqueteditor(
            data_source=data_source,
            data_target=data_target,
            force_overwrite=False,
        )
