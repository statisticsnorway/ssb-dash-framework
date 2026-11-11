import pandas as pd
import pytest

from ssb_dash_framework.experimental import MacroModuleDataHandler
from ssb_dash_framework.utils.alert_handler import AlertHandler


class StubMacroHandler(MacroModuleDataHandler):
    def __init__(self, data: pd.DataFrame) -> None:
        """Serve `data` for every period."""
        self.value_variables = {"omsetning": "Omsetning"}
        self.grouping_variables = ["naring"]
        self.data = data

    def fetch_observations(self, period: str) -> pd.DataFrame:
        return self.data.copy()


def observations(**overrides) -> pd.DataFrame:
    data = {
        "ident": ["a", "b"],
        "naring": ["01", None],
        "omsetning": [1.0, 2.0],
    }
    data.update(overrides)
    return pd.DataFrame(data)


@pytest.fixture
def warnings(monkeypatch) -> list[str]:
    messages: list[str] = []
    monkeypatch.setattr(AlertHandler, "warning", lambda msg, **_: messages.append(msg))
    return messages


def test_valid_observations_pass_through() -> None:
    data = StubMacroHandler(observations()).get_observations("2024")
    assert list(data["ident"]) == ["a", "b"]


def test_defaults_for_optional_methods() -> None:
    handler = StubMacroHandler(observations())
    assert handler.get_codelists("2024") == {}
    assert handler.last_updated("2024") is None


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (observations().drop(columns="naring"), "missing column(s) ['naring']"),
        (
            observations(omsetning=["1", "2"]),
            "value column 'omsetning' must be numeric",
        ),
        (
            observations(omsetning=[True, False]),
            "value column 'omsetning' must be numeric",
        ),
        (observations(naring=[1, 2]), "column 'naring' must contain strings"),
        (observations(ident=[1, 2]), "column 'ident' must contain strings"),
    ],
)
def test_structural_problems_raise(data: pd.DataFrame, message: str) -> None:
    with pytest.raises(ValueError, match="StubMacroHandler \\(period 2024\\)") as error:
        StubMacroHandler(data).get_observations("2024")
    assert message in str(error.value)


def test_non_dataframe_raises() -> None:
    handler = StubMacroHandler(observations())
    handler.fetch_observations = lambda period: [1, 2]  # type: ignore[method-assign]
    with pytest.raises(TypeError, match="must return a pandas DataFrame"):
        handler.get_observations("2024")


def test_duplicates_warn_then_raise(warnings: list[str]) -> None:
    handler = StubMacroHandler(observations(ident=["a", "a"]))
    with pytest.raises(ValueError, match="share a key"):
        handler.get_observations("2024")
    assert len(warnings) == 1
    assert "1 duplicate observation(s)" in warnings[0]


def test_instance_column_is_part_of_the_key(warnings: list[str]) -> None:
    data = observations(ident=["a", "a"], instance=["/g/0", "/g/1"])
    handler = StubMacroHandler(data)
    assert handler.key_columns(data) == ["ident", "instance"]
    assert len(handler.get_observations("2024")) == 2
    assert warnings == []


def test_resolve_duplicates_override_is_used() -> None:
    assert (
        len(KeepFirstHandler(observations(ident=["a", "a"])).get_observations("2024"))
        == 1
    )


class KeepFirstHandler(StubMacroHandler):
    def resolve_duplicates(self, data: pd.DataFrame, period: str) -> pd.DataFrame:
        return data.drop_duplicates("ident")
