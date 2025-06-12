from ssb_dash_framework import EditingTable
from ssb_dash_framework import MultiTable
from ssb_dash_framework import MultiTableTab
from ssb_dash_framework import MultiTableWindow


def test_import() -> None:
    assert MultiTable is not None
    assert MultiTableTab is not None
    assert MultiTableWindow is not None


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

    class test_implementation(MultiTable):
        def __init__(self, label, table_list) -> None:
            super().__init__(label=label, table_list=table_list)

        def layout(self):
            pass

    test_implementation(label="test multitable", table_list=[table1, table2])


def test_tab() -> None:

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

    MultiTableTab(label="test multitable", table_list=[table1, table2])


def test_window() -> None:

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

    MultiTableWindow(label="test multitable", table_list=[table1, table2])
