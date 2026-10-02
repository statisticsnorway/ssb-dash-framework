"""This serves as an example of a module."""

from abc import ABC
from abc import abstractmethod

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx

from ssb_dash_framework import AlertHandler
from ssb_dash_framework import ModuleBase
from ssb_dash_framework import VariableSelector

# from ..utils.


class HelloModuleMetaDataHandler(ABC):

    @abstractmethod
    def get_message(self, refnr):
        pass

    @abstractmethod
    def update_message(self, refnr, new_value):
        pass

    @abstractmethod
    def on_failure(self):
        pass


class HelloModuleDataHandlerDefault(HelloModuleMetaDataHandler):

    current_message: dict[str, str] = {
        "1": "Hello world!",
        "2": "Hello universe!",
    }

    def __init__(self) -> None:
        super().__init__()

    def get_message(self, refnr):
        if not refnr:
            raise ValueError(
                f"refnr cannot be none, put one of '{list(self.current_message.keys())}' in the variable selector!"
            )
        return HelloModuleDataHandlerDefault.current_message[refnr]

    def update_message(self, refnr, new_value):
        if not refnr:
            raise ValueError(
                f"refnr cannot be none, put one of '{list(self.current_message.keys())}' in the variable selector!"
            )
        HelloModuleDataHandlerDefault.current_message[refnr] = new_value

    def on_failure(self):
        return "An error happened, check the App-logg window for more information."


class HelloModuleDataHandlerCat(HelloModuleMetaDataHandler):

    cat = r"""
          |\__/,|   (`\
        _.|o o  |_   ) )
        -(((---(((--------
    """

    def get_message(self, refnr):
        return HelloModuleDataHandlerCat.cat

    def update_message(self, refnr, new_value):
        raise RuntimeError("The cat refuses to move!")

    def on_failure(self):
        return HelloModuleDataHandlerCat.cat


class HelloModule(ModuleBase):

    def __init__(self, label, data_handler: HelloModuleMetaDataHandler) -> None:

        self.label = label

        self.icon = ":)"

        self.data_handler = data_handler

        super().__init__()

    def _create_layout(self):
        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Button(
                            "Get currently stored message",
                            id=f"{self.module_id}-get-button",
                        ),
                        dbc.Button(
                            "Update stored message",
                            id=f"{self.module_id}-update-button",
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Textarea(
                                id=f"{self.module_id}-message-holder",
                                style={"height": "200px"},
                            )
                        )
                    ]
                ),
            ]
        )

    def layout(self):
        return self._create_layout()

    def module_callbacks(self):
        message_id = f"{self.module_id}-message-holder"
        get_id = f"{self.module_id}-get-button"
        update_id = f"{self.module_id}-update-button"

        @callback(
            Output(message_id, "value"),
            VariableSelector.get_refnr(State),
            Input(get_id, "n_clicks"),
            Input(update_id, "n_clicks"),
            State(message_id, "value"),
            prevent_initial_call=True,
        )
        def message_callback(refnr, get, update, textbox_content):

            if ctx.triggered_id == get_id:
                try:
                    to_return = self.data_handler.get_message(refnr)
                    AlertHandler.success("Returning message", ephemeral=True)
                except Exception as e:
                    AlertHandler.error(
                        f"Oh no! Something went wrong: {e}", ephemeral=True
                    )
                    to_return = self.data_handler.on_failure()

            if ctx.triggered_id == update_id:
                try:
                    current_message = self.data_handler.get_message(refnr)

                    if current_message != textbox_content:
                        self.data_handler.update_message(refnr, textbox_content)
                        to_return = self.data_handler.get_message(refnr)
                        AlertHandler.success(
                            f"Message changed from {current_message} to {textbox_content}",
                            ephemeral=True,
                        )
                    else:
                        raise RuntimeError("No change made!")
                except Exception as e:
                    AlertHandler.error(
                        f"Oh no! Something went wrong: {e}\n", ephemeral=True
                    )
                    to_return = self.data_handler.on_failure()

            return to_return
