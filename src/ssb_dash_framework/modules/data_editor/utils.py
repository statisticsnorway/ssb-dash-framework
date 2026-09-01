from typing import Literal

from pydantic import BaseModel


class EditorSettings(BaseModel):
    starting_table: str
    form_data_table: str
    form_list: list[str]
    refnr_col: str
    form_name_col: str
    ident_col: str
    field_value_col: str
    field_name_col: str
    period_col: str

    mapping_table: str = "mapping_variabelnavn"
    mapping_match_column: str = "variabel"
    mapping_result_column: str = "feltsti"

    table_selector_id: str | None = None
    form_selector_id: str | None = None


class RefnrStatus(BaseModel):
    active: bool
    status: Literal["Under arbeid", "Ferdig", "Ubehandlet"]
