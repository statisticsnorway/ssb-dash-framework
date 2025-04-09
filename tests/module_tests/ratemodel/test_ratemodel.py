def test_import():
    from ssb_dash_framework import RateModel
    from ssb_dash_framework import RateModelWindow

    # Verify that the import works
    assert RateModel is not None
    assert RateModelWindow is not None