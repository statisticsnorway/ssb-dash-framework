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
    )


def test_tab() -> None:
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


def test_get_update_data_calls():
    def get_data():
        return "Success"

    def update_data():
        return "Successfull update"

    table = EditingTable(  # Test without defining update function.
        label="test",
        inputs=[],
        states=[],
        get_data_func=get_data,
    )

    assert table.get_data() == "Success", "Error when getting data from function."

    table = EditingTable(
        label="test",
        inputs=[],
        states=[],
        get_data_func=get_data,
        update_table_func=update_data,
    )

    assert table.get_data() == "Success", "Error when getting data from function."
    assert table.update_table_func() == "Successfull update"
