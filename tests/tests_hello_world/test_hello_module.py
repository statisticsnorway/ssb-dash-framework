from ...demo.hello_world.hello_module import HelloModule
from ...demo.hello_world.hello_module import HelloModuleDataHandlerDefault
from ...demo.hello_world.hello_module import HelloModuleMetaDataHandler


def test_meta_data_handler():
    handler = HelloModuleMetaDataHandler()
    assert handler is not None

    class DummyMetaDataHandler(HelloModuleMetaDataHandler):

        def __init__(self):
            super().__init__()

        def get_message(self):
            return "Dummy message"

        def update_message(self, refnr: str, new_value: str):
            return f"New Dummy message {refnr}, {new_value}"

        def on_failure(self):
            raise Exception("Dummy failure")

    dummy_handler = DummyMetaDataHandler()
    assert dummy_handler.get_message() == "Dummy message"
    assert (
        dummy_handler.update_message("123", "New Value")
        == "New Dummy message 123, New Value"
    )
    try:
        dummy_handler.on_failure()
    except Exception as e:
        assert str(e) == "Dummy failure"


def test_data_handler_default():
    handler = HelloModuleDataHandlerDefault()
    assert handler is not None
    assert handler.get_message() == "Hello World"
    assert handler.update_message("123", "New Value") == "New Value"
    try:
        handler.on_failure()
    except Exception as e:
        assert (
            str(e)
            == "An error happened, check the App-logg window for more information."
        )


def test_hello_module():
    module = HelloModule(
        label="Test module", data_handler=HelloModuleDataHandlerDefault()
    )
    assert module is not None
