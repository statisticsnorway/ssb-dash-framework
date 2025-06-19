from ssb_dash_framework import EditingTable
from ssb_dash_framework import MultiModule
from ssb_dash_framework import MultiModuleTab
from ssb_dash_framework import MultiModuleWindow


def test_import() -> None:
    assert MultiModule is not None
    assert MultiModuleTab is not None
    assert MultiModuleWindow is not None


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

    class test_implementation(MultiModule):
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

    MultiModuleTab(label="test multitable", table_list=[table1, table2])


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

    MultiModuleWindow(label="test multitable", table_list=[table1, table2])
