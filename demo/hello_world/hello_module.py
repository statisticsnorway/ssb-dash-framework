"""This serves as an example of a module."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import ClassVar

import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import ctx
from dash import html
from dash.exceptions import PreventUpdate

from ssb_dash_framework import AlertHandler
from ssb_dash_framework import ModuleBase
from ssb_dash_framework import VariableSelector

# from ..utils.


class HelloModuleMetaDataHandler(ABC):
    """Abstract base class for handling metadata of the HelloModule."""

    @abstractmethod
    def get_message(self, refnr: str) -> str:
        """Retrieve the message for the given reference number."""
        ...

    @abstractmethod
    def update_message(self, refnr: str, new_value: str) -> str:
        """Update the message for the given reference number."""
        ...

    @abstractmethod
    def on_failure(self) -> Any:
        """Handle failure scenario."""
        ...


class HelloModuleDataHandlerDefault(HelloModuleMetaDataHandler):
    """Default implementation of the HelloModuleMetaDataHandler."""

    current_message: ClassVar[dict[str, str]] = {
        "1": "Hello world!",
        "2": "Hello universe!",
    }

    def __init__(self) -> None:
        """Initialize the default data handler."""
        super().__init__()

    def get_message(self, refnr: str) -> str:
        """Retrieve the message for the given reference number."""
        if not refnr:
            raise ValueError(
                f"refnr cannot be none, put one of '{list(self.current_message.keys())}' in the variable selector!"
            )
        return HelloModuleDataHandlerDefault.current_message[refnr]

    def update_message(self, refnr: str, new_value: str) -> str:
        """Update the message for the given reference number by modifying the classvar."""
        if not refnr:
            raise ValueError(
                f"refnr cannot be none, put one of '{list(self.current_message.keys())}' in the variable selector!"
            )
        HelloModuleDataHandlerDefault.current_message[refnr] = new_value
        return HelloModuleDataHandlerDefault.current_message[refnr]

    def on_failure(self) -> str:
        """Handle failure scenario by providing an error message."""
        return "An error happened, check the App-logg window for more information."


class HelloModuleDataHandlerCat(HelloModuleMetaDataHandler):
    """Implementation of the HelloModuleMetaDataHandler that always returns a cat ASCII art."""

    cat = r"""
          |\__/,|   (`\
        _.|o o  |_   ) )
        -(((---(((--------
    """

    def get_message(self, refnr: str) -> str:
        """Retrieve the cat ASCII art regardless of the reference number."""
        return HelloModuleDataHandlerCat.cat

    def update_message(self, refnr: str, new_value: str) -> str:
        """Attempting to update the message will always fail with a RuntimeError because the cat is stubborn."""
        raise RuntimeError("The cat refuses to move!")

    def on_failure(self) -> str:
        """Return the cat ASCII art in case of failure."""
        return HelloModuleDataHandlerCat.cat


class HelloModule(ModuleBase):
    """Implementation of the HelloModule that interacts with a data handler to manage messages."""

    def __init__(self, label: str, data_handler: HelloModuleMetaDataHandler) -> None:
        """Initialize the HelloModule with a label and a data handler."""
        self.label = label
        self.icon = ":)"
        self.data_handler = data_handler
        super().__init__()

    def _create_layout(self):
        """Create the layout for the HelloModule."""
        return html.Div(
            dbc.Container(
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
        )

    def layout(self) -> html.Div:
        """Return the layout for the HelloModule."""
        return self._create_layout()

    def module_callbacks(self) -> None:
        """Define the callbacks for the HelloModule."""
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
        def message_callback(
            refnr: str, get: int, update: int, textbox_content: str
        ) -> str:
            """Callback function to handle message retrieval and updates."""
            if ctx.triggered_id == get_id:
                try:
                    to_return = self.data_handler.get_message(refnr)
                    AlertHandler.success("Returning message", ephemeral=True)
                except Exception as e:
                    AlertHandler.error(
                        f"Oh no! Something went wrong: {e}", ephemeral=True
                    )
                    to_return = self.data_handler.on_failure()

            elif ctx.triggered_id == update_id:
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
            else:
                raise PreventUpdate

            return to_return
