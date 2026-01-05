import logging

import dash_bootstrap_components as dbc
from dash import callback
from dash import callback_context
from dash import html
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State
from mpmath import mp

logger = logging.getLogger(__name__)
mp.dps = 1000

pi = str(mp.pi)


class PimemorizerTab:
    """A tab for testing and improving memory of the digits of π (Pi).

    This component provides:
    - A text box to display the digits entered so far.
    - A numeric keypad to input digits.
    - A scoring system to track the current and high scores.

    Attributes:
        label (str): The label for the tab, set to "𝝅 Pi memorizer".
    """

    def __init__(
        self,
    ) -> None:
        """Initialize the PimemorizerTab component."""
        logger.warning(
            f"{self.__class__.__name__} is intended as a proof of concept for the flexibility of the framework, not as a production module."
        )
        self.label = "𝝅 Pi memorizer"
        self.callbacks()

    def layout(self) -> html.Div:
        """Generate the layout for the Pi memorizer tab.

        Returns:
            html.Div: A Div element containing:
                - A text area to display the user's current input sequence.
                - A numeric keypad for entering digits.
                - Score and high score displays to track progress.
        """
        layout = html.Div(
            style={"display": "grid", "grid-template-columns": "10% 70% 10% 10%"},
            children=[
                html.Div(),
                html.Div(
                    [
                        html.Div(
                            style={"margin-bottom": "20px"},
                            children=[
                                dbc.Textarea(
                                    id="text-box",
                                    size="xxl",
                                    value="3.",
                                ),
                            ],
                        ),
                        html.Div(
                            style={
                                "display": "grid",
                                "grid-template-columns": "repeat(3, 1fr)",
                                "gap": "10px",
                                "justify-content": "center",
                            },
                            children=[
                                dbc.Button(
                                    "1",
                                    id="pi-button1",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "2",
                                    id="pi-button2",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "3",
                                    id="pi-button3",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "4",
                                    id="pi-button4",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "5",
                                    id="pi-button5",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "6",
                                    id="pi-button6",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "7",
                                    id="pi-button7",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "8",
                                    id="pi-button8",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "9",
                                    id="pi-button9",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "",
                                    id="pi-button-empty1",
                                    color="secondary",
                                    disabled=True,
                                    style={
                                        "font-size": "20px",
                                        "padding": "20px",
                                        "grid-column": "span 1",
                                    },
                                ),
                                dbc.Button(
                                    "0",
                                    id="pi-button0",
                                    color="primary",
                                    style={"font-size": "20px", "padding": "20px"},
                                ),
                                dbc.Button(
                                    "",
                                    id="pi-button-empty2",
                                    color="secondary",
                                    disabled=True,
                                    style={
                                        "font-size": "20px",
                                        "padding": "20px",
                                        "grid-column": "span 1",
                                    },
                                ),
                            ],
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("Score", className="card-title"),
                                    html.Div(
                                        style={
                                            "display": "grid",
                                            "grid-template-columns": "100%",
                                        },
                                        children=[
                                            dbc.Input(
                                                value=0, id="score", type="number"
                                            ),
                                        ],
                                    ),
                                ],
                                style={"max-height": "100%"},
                            ),
                            style={"max-height": "100%"},
                        ),
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H5("High score", className="card-title"),
                                    html.Div(
                                        style={
                                            "display": "grid",
                                            "grid-template-columns": "100%",
                                        },
                                        children=[
                                            dbc.Input(
                                                value=0, id="highscore", type="number"
                                            ),
                                        ],
                                    ),
                                ],
                                style={"max-height": "100%"},
                            ),
                            style={"max-height": "100%"},
                        ),
                    ]
                ),
                html.Div(),
            ],
        )
        return layout

    def callbacks(self) -> None:
        """Register Dash callbacks for the Pi memorizer tab.

        Notes:
            - The `update_input` callback handles the interaction between the numeric keypad
              and the current sequence, score, and high score.
        """

        @callback(  # type: ignore[misc]
            Output("text-box", "value"),
            Output("score", "value"),
            Output("highscore", "value"),
            Input("pi-button0", "n_clicks"),
            Input("pi-button1", "n_clicks"),
            Input("pi-button2", "n_clicks"),
            Input("pi-button3", "n_clicks"),
            Input("pi-button4", "n_clicks"),
            Input("pi-button5", "n_clicks"),
            Input("pi-button6", "n_clicks"),
            Input("pi-button7", "n_clicks"),
            Input("pi-button8", "n_clicks"),
            Input("pi-button9", "n_clicks"),
            State("score", "value"),
            State("highscore", "value"),
            State("text-box", "value"),
        )
        def update_input(
            *args: dbc.Button,
            current_score: int,
            high_score: int,
            current_value: str,
        ) -> tuple[str, int, int]:
            """Update the input sequence, score, and high score based on user interaction.

            Args:
                *args: Clicks for numeric buttons (0-9).
                current_score: The current score of the user.
                high_score: The user's highest score so far.
                current_value: The current sequence of digits entered by the user.

            Returns:
                tuple: Contains:
                    - text-box (str): Updated sequence of digits.
                    - score (int): Updated current score.
                    - highscore (int): Updated high score.

            Notes:
                - If the user enters a correct digit sequence, the score increases.
                - If the sequence is incorrect, the score resets and the high score updates if necessary.
            """
            current_value = current_value or ""
            current_score = current_score or 0

            ctx = callback_context
            if not ctx.triggered:
                return current_value, current_score, current_score

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id.startswith("pi-button"):
                number = button_id[-1]
                new_string = current_value + number

            if new_string == pi[: int(current_score) + 3]:
                new_score = current_score + 1
                return new_string, new_score, high_score
            else:
                if current_score > high_score:
                    high_score = current_score
                current_value = "3."
                current_score = 0
                return current_value, current_score, high_score
