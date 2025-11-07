from ssb_dash_framework.setup.variableselector import VariableSelector


class ParquetEditor:
    _id_number: int = 0
    def __init__(self, id_vars, file_path) -> None:
        self.module_number = ParquetEditor._id_number
        self.module_name = self.__class__.__name__
        ParquetEditor._id_number += 1
        self.id_vars = id_vars
        self.variable_selector = VariableSelector(selected_inputs=id_vars, selected_states=[])
        self.file_path = file_path
        self.log_path = 
        self.label = file_path # Plukke ut filnavnet foran .parquet

        self.module_layout = self._create_layout()
        self.module_callbacks()
    
    def get_data(self):
        return pd.read_parquet(self.file_path)
    
    def _create_layout(self):
        return html.Div(
            dag.AgGrid(

            )
        )

    def layout(self):
        return html.Div(self.module_layout)
    
    def module_callbacks(self):
        @callback(
            Output(f"{self.module_number}-tabelleditering-table1", "rowData"),
            Output(f"{self.module_number}-tabelleditering-table1", "columnDefs"),
            *self.variable_selector.get_all_inputs()
        )
        def load_data_to_table(*args):
            data = self.get_data()
            columns = [
                {
                    "headerName": col,
                    "field": col,
                    "hide": col == "row_id",
                    "editable": col != "uuid",
                    "valueFormatter": (
                        {"function": self.number_format}
                        if pd.api.types.is_numeric_dtype(df[col])
                        else None
                    ),
                }
                for col in df.columns
            ]
            return data.to_dict, columns

@callback(  # type: ignore[misc]
                Output(f"{self.module_number}-pending-edit", "data"),
                Output(f"{self.module_number}-reason-modal", "is_open"),
                Output(f"{self.module_number}-edit-details", "children"),
                Output(f"{self.module_number}-edit-reason", "value"),
                Input(
                    f"{self.module_number}-tabelleditering-table1", "cellValueChanged"
                ),
                prevent_initial_call=True,
            )
            def capture_edit(
                edited: list[dict[str, Any]],
            ) -> tuple[dict[str, Any], bool, str, str]:
                if not edited:
                    raise PreventUpdate
                logger.info(edited)
                edit = edited[0]
                details = f"Column: {edit.get('colId')} | Old: {edit.get('oldValue')} | New: {edit.get('value')}"
                return edit, True, details, ""

            @callback(  # type: ignore[misc]
                Output(
                    f"{self.module_number}-reason-modal",
                    "is_open",
                    allow_duplicate=True,
                ),
                Output("alert_store", "data", allow_duplicate=True),
                Output(
                    f"{self.module_number}-table-data", "data", allow_duplicate=True
                ),
                Input(f"{self.module_number}-confirm-edit", "n_clicks"),
                Input(f"{self.module_number}-edit-reason", "n_submit"),
                State(f"{self.module_number}-pending-edit", "data"),
                State(f"{self.module_number}-edit-reason", "value"),
                State("alert_store", "data"),
                State(f"{self.module_number}-table-data", "data"),
                *dynamic_states,
                prevent_initial_call=True,
            )
            def confirm_edit(
                n_clicks: int,
                n_submit: int,
                pending_edit: dict[str, Any],
                reason: str,
                error_log: list[dict[str, Any]],
                table_data: list[dict[str, Any]],
                *dynamic_states: Any,
            ) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]:
                if not (n_clicks or n_submit):
                    raise PreventUpdate
                if not pending_edit:
                    error_log = [
                        create_alert(
                            "Ingen pending edit funnet", "error", ephemeral=True
                        ),
                        *error_log,
                    ]
                    return False, error_log, table_data
                if not reason or str(reason).strip() == "":
                    error_log = [
                        create_alert(
                            "Årsak for endring er påkrevd", "warning", ephemeral=True
                        ),
                        *error_log,
                    ]
                    return True, error_log, table_data

                edit_with_reason = dict(pending_edit)
                edit_with_reason["reason"] = reason.replace("\n", "")
                edit_with_reason["user"] = self.user
                edit_with_reason["change_event"] = "manual"

                aware_timestamp = datetime.now(self.tz)  # timezone-aware
                naive_timestamp = aware_timestamp.replace(tzinfo=None)  # drop tzinfo
                edit_with_reason["timestamp"] = naive_timestamp

                logger.debug(edit_with_reason)
                if self.log_filepath:
                    with open(self.log_filepath, "a", encoding="utf-8") as f:
                        f.write(
                            json.dumps(
                                edit_with_reason, ensure_ascii=False, default=str
                            )
                            + "\n"
                        )