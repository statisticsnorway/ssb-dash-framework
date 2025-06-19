from ssb_dash_framework import EditingTable
from ssb_dash_framework import EditingTableTab
from ssb_dash_framework import EditingTableWindow


def test_import() -> None:
    assert EditingTable is not None


def test_base_class() -> None:
    table1 = EditingTable(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
    )
    table2 = EditingTable(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
    )


def test_tab() -> None:

    EditingTableTab(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
    )
    EditingTableTab(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
    )


def test_window() -> None:

    EditingTableWindow(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
    )
    EditingTableWindow(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
    )
