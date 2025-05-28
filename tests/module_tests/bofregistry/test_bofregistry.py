from ssb_dash_framework import BofInformation


def test_import() -> None:
    assert BofInformation is not None


def test_initialization() -> None:
    class test_implementation(BofInformation):
        def __init__(self) -> None:
            super().__init__()

        def layout(self):
            pass

    test_implementation()
