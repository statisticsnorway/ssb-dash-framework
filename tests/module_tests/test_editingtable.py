from ssb_dash_framework import EditingTable
from ssb_dash_framework import EditingTableTab
from ssb_dash_framework import EditingTableWindow


def test_import() -> None:
    assert EditingTable is not None
    assert EditingTableTab is not None
    assert EditingTableWindow is not None


def test_base_class() -> None:
    EditingTable(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
        log_filepath="dummy.log",  # Add this line
    )


def test_tab() -> None:
    EditingTableTab(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
        log_filepath="dummy.log",  # Add this line
    )


def test_window() -> None:
    EditingTableWindow(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
        log_filepath="dummy.log",  # Add this line
    )
from ssb_dash_framework import EditingTable
from ssb_dash_framework import EditingTableTab
from ssb_dash_framework import EditingTableWindow


def test_import() -> None:
    assert EditingTable is not None
    assert EditingTableTab is not None
    assert EditingTableWindow is not None


def test_base_class() -> None:
    EditingTable(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
        log_filepath="dummy.log",  # Add this line
    )


def test_tab() -> None:
    EditingTableTab(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
        log_filepath="dummy.log",  # Add this line
    )


def test_window() -> None:
    EditingTableWindow(
        label="test",
        inputs=[],
        states=[],
        get_data_func=lambda x: x,
        log_filepath="dummy.log",  # Add this line
    )
