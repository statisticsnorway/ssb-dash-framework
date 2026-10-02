from pydantic import BaseModel

EDITING_CODE_DROPDOWN = lambda aio_id: f"{aio_id}-update-queue"


class EditorSettings(BaseModel):
    """Configuration model defining schema, table, and column mappings for the editor.

    Attributes:
        starting_table: Initial database table to load.
        form_data_table: Target table holding actual questionnaire form responses.
        form_list: List of allowed form/questionnaire identifiers.
        refnr_col: Column name representing submission reference numbers.
        form_name_col: Column representing form name (e.g. "skjema").
        ident_col: Column name representing respondent identifiers (e.g. "ident").
        field_value_col: Column containing form field values (e.g. "verdi").
        field_name_col: Column containing form field name paths (e.g. "feltsti").
        period_col: Column representing statistical period (e.g. "iso_period").
        mapping_table: Table used for mapping variables. Defaults to "mapping_variabelnavn".
        mapping_match_column: Match column in mapping table. Defaults to "variabel".
        mapping_result_column: Result column in mapping table. Defaults to "feltsti".
        table_selector_id: Custom Dash ID for the table dropdown selector.
        form_selector_id: Custom Dash ID for the form dropdown selector.
    """
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
