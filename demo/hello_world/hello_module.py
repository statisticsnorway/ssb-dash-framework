"""This serves as an example of a module."""

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import clientside_callback
from dash import dcc
from dash import html, callback
from abc import abstractmethod, ABC
from dash import callback, Input, Output, ctx, State
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
        AlertHandler._add_alert("A cat has appeared!", color="success", ephemeral=True, position="center")
        return HelloModuleDataHandlerCat.cat

    def update_message(self, new_value):
        raise RuntimeError("Oh no, the cat refuses to move!")


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
                            "Get currently stored message",
                            id=f"{self.module_name}-{self.module_number}-get-button",
                        ),
                        dbc.Button(
                            "Update stored message",
                            id=f"{self.module_name}-{self.module_number}-update-button",
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Textarea(
                                id=f"{self.module_name}-{self.module_number}-message-holder",
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
        message_id = f"{self.module_name}-{self.module_number}-message-holder"
        get_id = f"{self.module_name}-{self.module_number}-get-button"
        refresh_id = f"{self.module_name}-{self.module_number}-update-button"

        @callback(
            Output(message_id, "value"),
            Input(get_id, "n_clicks"),
            Input(refresh_id, "n_clicks"),
            State(message_id, "value"),
            prevent_initial_call=True,
        )
        def message_callback(get, update, new_message):

            if ctx.triggered_id == get_id:
                try:
                    to_return = self.data_handler.get_message()
                    AlertHandler.success("Returning message", ephemeral=True)
                except Exception as e:
                    AlertHandler.error(
                        f"Oh no! Something went wrong: {e}", ephemeral=True
                    )
                    raise PreventUpdate

            if ctx.triggered_id == refresh_id:
                try:
                    current_message = self.data_handler.get_message()

                    if current_message != new_message:
                        self.data_handler.update_message(new_message)
                        to_return = self.data_handler.get_message()
                        AlertHandler.success(
                            f"Message changed from {current_message} to {new_message}",
                            ephemeral=True,
                        )
                    else:
                        raise RuntimeError("No change made!")
                except Exception as e:
                    AlertHandler.error(
                        f"Oh no! Something went wrong: {e}", ephemeral=True
                    )
                    raise PreventUpdate

            return to_return
