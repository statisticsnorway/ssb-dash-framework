def test_import_freesearch() -> None:
    from ssb_dash_framework import FreeSearch
    from ssb_dash_framework import FreeSearchTab
    from ssb_dash_framework import FreeSearchWindow

    # Verify that the import works
    assert FreeSearch is not None
    assert FreeSearchTab is not None
    assert FreeSearchWindow is not None
