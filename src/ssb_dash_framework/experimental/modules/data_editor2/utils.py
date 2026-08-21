

from typing import Literal, Type

from pydantic import BaseModel

class EditorSettings(BaseModel):
    starting_table: str
    form_data_tables: list[str]
    form_list: list[str]
    refnr_col: str
    form_name_col: str
    ident_col: str
    field_value_col: str
    field_name_col: str
    period_col: str

class RefnrStatus(BaseModel):
    active: bool
    status: Literal["Under arbeid", "Ferdig", "Ubehandlet"]