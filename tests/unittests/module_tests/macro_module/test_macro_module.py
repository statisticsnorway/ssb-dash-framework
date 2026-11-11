import numpy as np
import pandas as pd
import pytest

from ssb_dash_framework import VariableSelector
from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework.experimental import AltinnMacroModuleDataHandler
from ssb_dash_framework.experimental import MacroModule
from ssb_dash_framework.experimental import MacroModuleDataHandler
from ssb_dash_framework.modules.macro_module.macro_module import COUNT
from ssb_dash_framework.modules.macro_module.macro_module import DIFF
from ssb_dash_framework.modules.macro_module.macro_module import PREV
from ssb_dash_framework.modules.macro_module.macro_module import SHOWN
from ssb_dash_framework.modules.macro_module.macro_module import STATUS
from ssb_dash_framework.modules.macro_module.macro_module import UNKNOWN
from ssb_dash_framework.modules.macro_module.macro_module import add_display_columns
from ssb_dash_framework.modules.macro_module.macro_module import add_group_labels
from ssb_dash_framework.modules.macro_module.macro_module import apply_filters
from ssb_dash_framework.modules.macro_module.macro_module import comparison_period
from ssb_dash_framework.modules.macro_module.macro_module import macro_table
from ssb_dash_framework.modules.macro_module.macro_module import observation_list
from ssb_dash_framework.modules.macro_module.macro_module import prepare
from ssb_dash_framework.modules.macro_module.macro_module import totals
from ssb_dash_framework.setup.variableselector import TimeUnit

SELECTOR_STATE = (
    "_time_unit",
    "_ident",
    "_refnr",
    "_secondary_ident",
    "_grouping_variables",
)

CURRENT = pd.DataFrame(
    {
        "ident": ["a", "b", "c", "d"],
        "naring": ["01", "02", "01", None],
        "kommune": ["0301", "0301", "1103", "0301"],
        "omsetning": [10.0, 20.0, 30.0, 5.0],
        "ansatte": [1.0, 2.0, 3.0, 1.0],
    }
)
COMPARISON = pd.DataFrame(
    {
        "ident": ["a", "b", "c", "e"],
        "naring": ["01", "01", "01", "03"],
        "kommune": ["0301", "0301", "1103", "0301"],
        "omsetning": [8.0, 15.0, 30.0, 4.0],
        "ansatte": [1.0, 2.0, 2.0, 1.0],
    }
)
CODELISTS = {"naring": {"02": "Skogbruk", "01": "Jordbruk"}}
VALUES = ["omsetning", "ansatte"]


class StubModuleHandler(MacroModuleDataHandler):
    value_variables = {"omsetning": "Omsetning", "ansatte": "Ansatte"}  # noqa: RUF012
    grouping_variables = ["naring", "kommune"]  # noqa: RUF012

    def fetch_observations(self, period: str) -> pd.DataFrame:
        return CURRENT if period == "2024" else COMPARISON


class BadNamesHandler(StubModuleHandler):
    grouping_variables = ["ident"]  # noqa: RUF012


@pytest.fixture
def selector():
    saved = {name: getattr(VariableSelector, name) for name in SELECTOR_STATE}
    for name in SELECTOR_STATE:
        setattr(VariableSelector, name, None)
    VariableSelectorConfig(
        ident="ident",
        time_units={"name": "periode", "frequency": "year"},
        grouping_variables=["naring"],
    )
    yield
    for name, value in saved.items():
        setattr(VariableSelector, name, value)


def prepared(data: pd.DataFrame) -> pd.DataFrame:
    return prepare(data, ["naring", "kommune"], VALUES, CODELISTS)[0]


def test_comparison_period() -> None:
    year = TimeUnit(name="aar", frequency="year")
    month = TimeUnit(name="periode", frequency="month")
    assert comparison_period(year, "2024", 1) == "2023"
    assert comparison_period(month, "2026-03", 12) == "2025-03"


def test_prepare_marks_unknown_codes() -> None:
    data, unknown = prepare(COMPARISON, ["naring"], VALUES, CODELISTS)
    assert list(data["naring"]) == ["01", "01", "01", UNKNOWN]
    assert unknown == 1
    data, unknown = prepare(CURRENT, ["naring"], VALUES, {})
    assert list(data["naring"]) == ["01", "02", "01", UNKNOWN]
    assert unknown == 1


def test_apply_filters() -> None:
    assert list(
        apply_filters(CURRENT, {"naring": "01", "kommune": "0301"})["ident"]
    ) == ["a"]
    assert len(apply_filters(CURRENT, {})) == 4


def test_macro_table_sums_counts_and_orders_by_codelist() -> None:
    table = macro_table(
        prepared(CURRENT), prepared(COMPARISON), ["naring"], VALUES, CODELISTS
    )
    assert list(table["naring"]) == ["02", "01", UNKNOWN]
    assert list(table[COUNT]) == [1, 2, 1]
    assert list(table["omsetning"]) == [20.0, 40.0, 5.0]
    assert list(table["omsetning" + PREV]) == [0.0, 53.0, 4.0]


def test_macro_table_keeps_groups_only_in_comparison_period() -> None:
    table = macro_table(
        prepared(CURRENT), prepared(COMPARISON), ["kommune"], VALUES, {}
    )
    assert list(table["kommune"]) == ["0301", "1103"]
    current = prepared(CURRENT)[lambda d: d["kommune"] == "0301"]
    table = macro_table(current, prepared(COMPARISON), ["kommune"], VALUES, {})
    assert list(table["kommune"]) == ["0301", "1103"]
    assert list(table[COUNT]) == [3, 0]


def test_macro_table_show_empty_adds_every_combination() -> None:
    args = (
        prepared(CURRENT),
        prepared(COMPARISON),
        ["naring", "kommune"],
        VALUES,
        CODELISTS,
    )
    assert len(macro_table(*args)) == 4
    full = macro_table(*args, show_empty=True)
    assert len(full) == 6
    assert list(full["naring"]) == ["02", "02", "01", "01", UNKNOWN, UNKNOWN]


def test_macro_table_without_grouping_is_empty() -> None:
    assert macro_table(prepared(CURRENT), prepared(COMPARISON), [], VALUES, {}).empty


def test_totals() -> None:
    total = totals(prepared(CURRENT), prepared(COMPARISON), VALUES).iloc[0]
    assert total[COUNT] == 4
    assert total["omsetning"] == 65.0
    assert total["omsetning" + PREV] == 57.0


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("pct", [1.0, -0.5, np.nan]),
        ("diff", [5.0, -5.0, 3.0]),
        ("current", [10.0, 5.0, 3.0]),
    ],
)
def test_display_modes(mode: str, expected: list[float]) -> None:
    table = pd.DataFrame(
        {"omsetning": [10.0, 5.0, 3.0], "omsetning" + PREV: [5.0, 10.0, 0.0]}
    )
    shown = add_display_columns(table, ["omsetning"], mode, "2024", "2023")
    np.testing.assert_array_equal(shown["omsetning" + SHOWN], expected)
    assert shown["omsetning__tooltip"][0] == "2024: 10\n2023: 5\nEndring: +5"


def test_group_labels() -> None:
    table = pd.DataFrame({"naring": ["01", UNKNOWN]})
    labelled = add_group_labels(table, ["naring"], CODELISTS)
    assert list(labelled["naring" + SHOWN]) == ["01 Jordbruk", UNKNOWN]


def test_observation_list_statuses_and_contributions() -> None:
    data = observation_list(
        prepared(CURRENT),
        prepared(COMPARISON),
        ["ident"],
        {"naring": "01"},
        VALUES,
        "omsetning",
    )
    rows = data.set_index("ident")
    assert dict(rows[STATUS]) == {"a": "", "b": "Ut", "c": ""}
    assert dict(rows["omsetning" + DIFF]) == {"a": 2.0, "b": -15.0, "c": 0.0}
    assert list(data["ident"]) == ["b", "c", "a"]


def test_observation_list_new_and_gone() -> None:
    current = prepared(CURRENT)
    comparison = prepared(COMPARISON)
    gone = observation_list(
        current, comparison, ["ident"], {"naring": UNKNOWN}, VALUES, "omsetning"
    )
    assert dict(zip(gone["ident"], gone[STATUS], strict=True)) == {
        "d": "Ny",
        "e": "Borte",
    }
    moved_in = observation_list(
        current, comparison, ["ident"], {"naring": "02"}, VALUES, "omsetning"
    )
    assert dict(zip(moved_in["ident"], moved_in[STATUS], strict=True)) == {"b": "Inn"}


def test_observation_list_reverse_and_increase_order() -> None:
    args = (
        prepared(CURRENT),
        prepared(COMPARISON),
        ["ident"],
        {"kommune": "0301"},
        VALUES,
        "omsetning",
    )
    assert list(observation_list(*args)["ident"]) == ["b", "d", "a", "e"]
    assert list(observation_list(*args, reverse=True)["ident"]) == ["e", "a", "b", "d"]


def test_observation_list_with_instances() -> None:
    current = pd.DataFrame(
        {
            "ident": ["a", "a"],
            "instance": ["/g/0", "/g/1"],
            "kode": ["x", "y"],
            "v": [1.0, 2.0],
        }
    )
    comparison = current.assign(v=[1.0, 1.0])
    data = observation_list(
        current, comparison, ["ident", "instance"], {"kode": "y"}, ["v"], "v"
    )
    assert list(data["instance"]) == ["/g/1"]
    assert list(data["v" + DIFF]) == [1.0]


@pytest.mark.usefixtures("selector")
def test_module_builds_layout_and_filters() -> None:
    module = MacroModule(StubModuleHandler(), comparison_lag=2)
    assert module.grouping_variables == ["naring", "kommune"]
    assert module.filter_variables == ["naring"]
    assert module.module_id in str(module.layout())


@pytest.mark.usefixtures("selector")
def test_module_grouping_variables_argument() -> None:
    module = MacroModule(StubModuleHandler(), grouping_variables=["kommune"])
    assert module.grouping_variables == ["kommune"]
    assert module.filter_variables == []


@pytest.mark.usefixtures("selector")
@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"data_handler": object()}, TypeError, "must be a MacroModuleDataHandler"),
        (
            {"grouping_variables": ["fylke"]},
            ValueError,
            "does not declare the grouping variable",
        ),
        ({"comparison_lag": 0}, ValueError, "comparison_lag"),
        ({"data_handler": BadNamesHandler()}, ValueError, "must be unique"),
    ],
)
def test_module_rejects_bad_configuration(kwargs, error, message) -> None:
    kwargs = {"data_handler": StubModuleHandler(), **kwargs}
    with pytest.raises(error, match=message):
        MacroModule(**kwargs)


def test_module_requires_time_unit_and_ident(selector) -> None:
    VariableSelector._ident = None
    with pytest.raises(ValueError, match="'time_units' and 'ident'"):
        MacroModule(StubModuleHandler())


@pytest.mark.usefixtures("selector")
def test_from_yaml_builds_the_data_handler() -> None:
    module = MacroModule.from_yaml(
        as_type="Tab",
        label="Makro",
        data_handler={
            "type": "AltinnMacroModuleDataHandler",
            "skjema": "RA-0745",
            "value_variables": ["NyEngArbAreal"],
            "grouping_variables": ["naring"],
        },
    )
    assert isinstance(module.data_handler, AltinnMacroModuleDataHandler)
    assert module.label == "Makro"


@pytest.mark.usefixtures("selector")
def test_from_yaml_rejects_other_handlers() -> None:
    with pytest.raises(TypeError, match="not a MacroModuleDataHandler"):
        MacroModule.from_yaml(data_handler="StandardDataHandler")
