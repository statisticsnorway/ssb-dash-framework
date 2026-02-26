import logging

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Input
from dash import Output
from dash import State
from dash import callback
from dash import dcc
from dash import html

from ...utils.module_validation import module_validator

logger = logging.getLogger(__name__)


class BulkEditor:
    _id_number: int = 0

    def __init__(self, header: str | None, context_fields, conn=None) -> None:
        self.module_number = BulkEditor._id_number
        self.module_name = self.__class__.__name__
        BulkEditor._id_number += 1

        self.header = header
        self.module_layout = self._create_layout()
        module_validator(self)

    def _create_layout(self):
        commit_modal = (
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Header")),
                    dbc.ModalBody(
                        [
                            dbc.Row(
                                "Preview edits here.",
                                id=f"{self.module_number}-bulk-edits-preview",
                            ),
                            dbc.Row(
                                dbc.Button(id=f"{self.module_number}-commit-action")
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="close", className="ms-auto", n_clicks=0)
                    ),
                ],
                id="modal",
                is_open=False,
            ),
        )

        html.Div(
            [
                dcc.Store(id=f"{self.module_number}-stored-edits"),
                dcc.Store(id=f"{self.module_number}-stored-starting-point"),
                commit_modal,
                dbc.Row(html.H1(self.header)) if self.header else html.Div(),
                dbc.Row([*context_fields]),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                id=f"{self.module_number}-bulk-commit-open",
                                children="Commit 0 changes",
                            )
                        )
                    ]
                ),
                dbc.Row(dag.AgGrid(id=f"{self.module_number}-bulk-table")),
            ]
        )

    def layout(self):
        return self.module_layout

    def get_data(self): ...

    def apply_update(self, single_update_dict):
        """Method to apply an edit to the database."""
        ...

    def module_callbacks(self):

        @callback()
        def start_table(): ...

        @callback(
            [
                Output(f"{self.module_number}-bulk-commit-open", "children"),
                Output(f"{self.module_number}-stored-edits", "data"),
                Input(f"{self.module_number}-bulk-table", "cellValueChanged"),
                State(f"{self.module_number}-stored-edits", "data"),
            ]
        )
        def add_edit_to_bulk(fresh_edit, stored_edits):
            logger.info("Adding new edit to stored edits")
            logger.debug(f"Fresh edit:\n{fresh_edit}\nstored_edits: \n{stored_edits}")
            return f"Commit {len(stored_edits)} changes", stored_edits

        @callback(
            Output(f"{self.module_number}-bulk-edits-preview", "children"),
            Input(f"{self.module_number}-stored-edits", "data"),
        )
        def preview_commit(): ...

        @callback(
            #            Output() # Alerts
            Input(f"{self.module_number}-commit-action", "n_clicks"),
            State(f"{self.module_number}-stored-edits", "data"),
        )
        def commit_changes(click, stored_edits):
            for edit in stored_edits:
                self.apply_update(edit)

        @callback()
        def revert_to_start(): ...
