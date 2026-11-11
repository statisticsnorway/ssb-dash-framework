import pandas as pd
import pytest

from ssb_dash_framework.experimental import AltinnMacroModuleDataHandler

AREAL = "NyEngArbAreal"
MENGDE = "NyEngSpredUtsGjodsMengde"
SKIP_TOTALS = {"NyEngSpredUtsID": ["TOTAL_ROW"]}


def per_unit(**kwargs) -> AltinnMacroModuleDataHandler:
    args = {
        "skjema": "RA-0745",
        "value_variables": {AREAL: "Areal", MENGDE: "Mengde"},
        "grouping_variables": ["naring", "kommune"],
        "exclude_instances": SKIP_TOTALS,
    }
    return AltinnMacroModuleDataHandler(**{**args, **kwargs})


def by_ident(data: pd.DataFrame, column: str) -> dict:
    return dict(zip(data["ident"], data[column], strict=True))


def test_per_unit_observations() -> None:
    data = per_unit().get_observations("2026")
    assert by_ident(data, AREAL) == {
        "ATF2134660": 57.0,
        "ATF2134661": 58.0,
        "ATF2134662": 50.0,
    }
    assert by_ident(data, MENGDE) == {
        "ATF2134660": 144.0,
        "ATF2134661": 146.0,
        "ATF2134662": 130.0,
    }
    assert by_ident(data, "naring") == {
        "ATF2134660": "01.11",
        "ATF2134661": "01.11",
        "ATF2134662": "01.41",
    }
    assert by_ident(data, "name")["ATF2134660"] == "KVITSØY OG RØST REVISJON"
    assert "instance" not in data.columns


def test_grouping_values_follow_the_period() -> None:
    assert (
        by_ident(per_unit().get_observations("2025"), "naring")["ATF2134661"] == "01.41"
    )


def test_summary_instances_are_excluded() -> None:
    with_totals = per_unit(exclude_instances=None).get_observations("2026")
    without = per_unit().get_observations("2026")
    assert (with_totals[MENGDE] > without[MENGDE]).all()


def test_instance_observations() -> None:
    handler = AltinnMacroModuleDataHandler(
        skjema="RA-0745",
        value_variables=[MENGDE],
        grouping_variables=["NyEngSpredUtsID", "naring"],
        repeating_group="/NyEngSpredUtsGroup/",
        exclude_instances=SKIP_TOTALS,
    )
    data = handler.get_observations("2026")
    unit = data[data["ident"] == "ATF2134660"].set_index("instance")
    assert sorted(unit.index) == ["/NyEngSpredUtsGroup/0", "/NyEngSpredUtsGroup/9"]
    assert dict(unit["NyEngSpredUtsID"]) == {
        "/NyEngSpredUtsGroup/0": "00",
        "/NyEngSpredUtsGroup/9": "09",
    }
    assert unit[MENGDE].sum() == 144.0
    assert set(unit["naring"]) == {"01.11"}


def test_only_active_submissions_are_used() -> None:
    handler = AltinnMacroModuleDataHandler(
        skjema="RA-0187",
        value_variables=["omsVirksomhetPerioden"],
        grouping_variables=["enhetsType"],
    )
    data = handler.get_observations("2026-01")
    assert by_ident(data, "omsVirksomhetPerioden")["12111111"] == 6007.0
    assert by_ident(data, "enhetsType")["12111111"] == "BEDR"


def test_latest_active_submission_wins() -> None:
    data = pd.DataFrame(
        {
            "ident": ["a", "a", "a", "b"],
            "instance": ["/g/0", "/g/1", "/g/0", "/g/0"],
            "refnr": ["old", "old", "new", "only"],
            "dato_mottatt": ["2024-01-01", "2024-01-01", "2024-02-01", "2024-01-01"],
        }
    )
    kept = per_unit().resolve_duplicates(data, "2024")
    assert list(kept["refnr"]) == ["new", "only"]


def test_empty_period_has_all_columns() -> None:
    data = per_unit().get_observations("2020")
    assert data.empty
    assert {"ident", "name", "naring", "kommune", AREAL, MENGDE} <= set(data.columns)


def test_non_numeric_values_raise() -> None:
    handler = per_unit(value_variables=["prefillVekstNavn"])
    with pytest.raises(ValueError, match="non-numeric value"):
        handler.get_observations("2026")


def test_last_updated() -> None:
    assert per_unit().last_updated("2026") == "2026-12-17 09:22:44"
    assert per_unit().last_updated("2020") is None


def test_codelists(monkeypatch) -> None:
    class FakeKlass:
        def __init__(self, classification_id: int) -> None:
            assert classification_id == 6

        def get_codes(self, from_date: str, select_level: int | None = None):
            assert (from_date, select_level) == ("2026-12-31", 2)
            return type(
                "Codes",
                (),
                {"data": pd.DataFrame({"code": ["01"], "name": ["Jordbruk"]})},
            )

    monkeypatch.setattr("klass.KlassClassification", FakeKlass)
    handler = per_unit(
        codelists={"naring": {"klass": 6, "level": 2}, "kommune": ["3411", 1121]}
    )
    assert handler.get_codelists("2026") == {
        "naring": {"01": "Jordbruk"},
        "kommune": {"3411": "3411", "1121": "1121"},
    }
    handler = per_unit(codelists={"naring": {"01.11": "Korn"}})
    assert handler.get_codelists("2026") == {"naring": {"01.11": "Korn"}}


@pytest.mark.parametrize(
    ("codelists", "message"),
    [
        ({"fylke": ["03"]}, "not a grouping variable"),
        ({"naring": "01"}, "must be a list or a dict"),
    ],
)
def test_bad_codelists_raise(codelists, message) -> None:
    with pytest.raises(ValueError, match=message):
        per_unit(codelists=codelists)
