"""This serves as an example of a module."""

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import clientside_callback
from dash import dcc
from dash import html, callback
from abc import abstractmethod, ABC
from dash import callback, Input, Output, ctx
from dash.exceptions import PreventUpdate
from ssb_dash_framework import AlertHandler

# from ..utils.


class HelloModuleMetaDataHandler(ABC):

    @abstractmethod
    def get_message(self):
        pass

    @abstractmethod
    def update_message(self, new_value):
        pass


class HelloModuleDataHandlerDefault(ABC):

    current_message = "Hello world!"

    def __init__(self) -> None:
        super().__init__()

    def get_message(self):
        return HelloModuleDataHandlerDefault.current_message

    def update_message(self, new_value):
        HelloModuleDataHandlerDefault.current_message = new_value


class HelloModuleDataHandlerCat(ABC):

    cat = r"""
          |\__/,|   (`\
        _.|o o  |_   ) )
        -(((---(((--------
    """

    def get_message(self):
        return HelloModuleDataHandlerCat.cat

    def update_message(self, new_value):
        AlertHandler.error("Oh no, the cat refuses to change!")


class HelloModule:
    _id_number = 0

    def __init__(self, label, data_handler: HelloModuleMetaDataHandler) -> None:
        self.module_number = HelloModule._id_number
        self.module_name = self.__class__.__name__
        HelloModule._id_number += 1

        self.label = label

        self.icon = ":)"

        self.data_handler = data_handler

        self.module_callbacks()

    def _create_layout(self):
        return dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Button(
                            "Update message",
                            id=f"{self.module_name}-{self.module_number}-update-button",
                        )
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Textarea(
                                id=f"{self.module_name}-{self.module_number}-message-holder",
                                value=self.data_handler.get_message(),
                                style={"height": "200px"}
                            )
                        )
                    ]
                ),
            ]
        )

    def layout(self):
        return self._create_layout()

    def module_callbacks(self):
        message_id = f"{self.module_name}-{self.module_number}-message-holder"
        refresh_id = f"{self.module_name}-{self.module_number}-update-button"

        @callback(
            Output(message_id, "value"),
            Input(refresh_id, "n_clicks"),
            Input(message_id, "value"),
            prevent_initial_call=True,
        )
        def message_callback(n_clicks, new_message):

            if ctx.triggered_id == refresh_id:
                return self.data_handler.get_message()

            if ctx.triggered_id == message_id:
                current_message = self.data_handler.get_message()

                if current_message != new_message:
                    self.data_handler.update_message(new_message)

                raise PreventUpdate

            raise PreventUpdate
