import logging
from collections.abc import Callable
from typing import Any
from typing import Literal

from dash.exceptions import PreventUpdate
from ibis import _
from psycopg_pool import ConnectionPool
from pydantic import BaseModel

from ..utils import AlertHandler
from .config_tools.connection import _get_connection_object
from .config_tools.connection import get_connection

logger = logging.getLogger(__name__)


def _is_valid_int(v: Any) -> bool | str:
    """Valid only if the string content is a whole number with no decimal separator."""
    s = str(v).strip()
    if "." in s or "," in s:
        return "float"
    if s.lstrip("-").isdigit() and s not in ("", "-"):
        return True
    return False


def _is_valid_bool(v: Any) -> bool:
    """Accepts 'true'/'false' (any case), and '1'/'0'."""
    s = str(v).strip().lower()
    return s in {"true", "false", "1", "0"}


_VALIDATORS: dict[str, Callable[[Any], str | None | bool]] = {
    "string": lambda v: True,
    "integer": _is_valid_int,
    "number": _is_valid_int,
    "bool": _is_valid_bool,
}


class UpdateSkjemamottak(BaseModel):
    """Class to update editing status in table 'skjemamottak' for a refnr, runs after user edits 'status'.
    Also runs after skjemadata edits (if on_skjemadata_update = True) for postgreSQL connections:
        - If status currently is 'Ubehandlet', it updates the status to 'Under arbeid'. Other statuses are ignored.

    Args:
        refnr (str): Reference number identifying the row.
        column (str): Column that will be updated, usually 'status' (str option in new model) or 'editert' (boolean in old model).
        value (Any): New value to write. For new model it includes: Literal["Ubehandlet", "Under arbeid", "Ferdig"].
    """

    refnr: str
    column: str
    value: str | bool
    on_skjemadata_update: bool = False

    def __str__(self) -> str:
        return (
            "Update to apply:\n"
            f"  refnr  : {self.refnr}\n"
            f"  value  : {self.value}\n"
            f"  column : {self.column}\n"
            f"  on_skjemadata_update : {self.on_skjemadata_update}\n"
        )

    def _current_status(self, conn) -> str:
        return (
            conn.table("skjemamottak")
            .filter(_.refnr == self.refnr)
            .select(self.column)
            .limit(1)
            .execute()[self.column]
            .item()
        )

    def _sql_value(self) -> str:
        return f"'{self.value}'"

    def update_ibis(self) -> bool:
        """Applies the update. Returns True if a row was changed, False if skipped."""

        with get_connection() as conn:
            if self.on_skjemadata_update:
                current = self._current_status(conn)
                logger.debug(f"Current status for {self.refnr}: {current!r}")
                if current != "Ubehandlet":
                    logger.debug(
                        f"Skipping status update, current status is {current!r}"
                    )
                    return False

            query = f"""
                UPDATE skjemamottak
                SET {self.column} = {self._sql_value()}
                WHERE refnr = '{self.refnr}'
            """

            logger.debug(f"Running query: {query}")
            try:
                conn.raw_sql(query)
                return True
            except Exception as e:
                logger.debug(f"Update failed: {e}")
                return False


class UpdateSkjemamottakAktiv(UpdateSkjemamottak):
    value: bool
    column: Literal["aktiv"] = "aktiv"
    
    def _sql_value(self) -> str:
        return "TRUE" if self.value else "FALSE"

class UpdateSkjemamottakKommentar(UpdateSkjemamottak):
    value: str
    column: Literal["kommentar"] = "kommentar"


class UpdateSkjemadata(BaseModel):
    """Model to centralize logic for updating data.

    Args:
        table (str): Name of the table being updated.
        skjema (str): Type of Altinn3 RA-skjema to insert on.
        ident (str): Identity of unit being updated.
        identifier_column (str): Identifying column to refer to for updates. Usually refnr, ident for non-Altinn3 data.
        refnr (str): Reference number identifying the row.
        time_units (str): Time unit.
        period (str): Time unit period to filter by.
        column (str): Column that will be updated.
        variable (str): Variable associated with the column. Note, this is identical to column if the table is not in the long format.
        value (Any): New value to write.
        old_value (Any): Previous value in the database.
        long (bool): Whether the database table is in the long format or not.
        mapping_table (str): Lookup table mapping a variable's short name to its long name (feltsti), used by the skjemadata INSERT-fallback. Defaults to "mapping_variabelnavn".
        mapping_match_column (str): Column in mapping_table matched against `variable` (the short name). Defaults to "variabel".
        mapping_result_column (str): Column in mapping_table returned as the long name. Defaults to "feltsti".
    """

    table: str
    skjema: str | None = None
    ident: str
    identifier_column: str = "refnr"
    refnr: str
    time_units: str | None = None
    period: str | None = None
    column: str
    variable: str
    value: Any
    old_value: Any
    long: bool
    mapping_table: str = "mapping_variabelnavn"
    mapping_match_column: str = "variabel"
    mapping_result_column: str = "feltsti"

    def __str__(self) -> str:
        return (
            "Update to apply:\n"
            f"  Table             : {self.table}\n"
            f"  Skjema            : {self.skjema}\n"
            f"  Table Type        : {'long' if self.long else 'wide'}\n"
            f"  Ident             : {self.ident}\n"
            f"  Identifier column : {self.identifier_column}\n"
            f"  RefNr             : {self.refnr}\n"
            f"  Time Units        : {self.time_units}\n"
            f"  Period            : {self.period}\n"
            f"  Column            : {self.column}\n"
            f"  Variable          : {self.variable}\n"
            f"  Value             : {self.old_value} -> {self.value}"
        )

    def to_alert(self, long, success: bool, datatype: str | None = None):

        if datatype:
            if datatype == "float":
                AlertHandler.warning(
                    msg=f"Feilet oppdatering av ident '{self.ident}' på variabel '{self.variable if long else self.column}' fra '{self.old_value}' til '{self.value}': "
                    f"Heltallsfelt kan ikke inneholde komma eller punktum (fikk '{self.value}').",
                    ephemeral=True,
                )
            else:
                AlertHandler.warning(
                    f"Feilet oppdatering av ident '{self.ident}' på variabel '{self.variable if long else self.column}' fra '{self.old_value}' til '{self.value}': Datatypen skal være {datatype}, ikke {type(self.value)}.",
                    ephemeral=True,
                )
            return

        if success:
            AlertHandler.success(
                f"Ident '{self.ident}' oppdatert på variabel '{self.variable if long else self.column}' fra '{self.old_value}' til '{self.value}'!",
                ephemeral=True,
            )
        else:
            AlertHandler.warning(
                f"Feilet oppdatering av ident '{self.ident}' på variabel '{self.variable if long else self.column}' fra '{self.old_value}' til '{self.value}'. Se logg for detaljer.",
                ephemeral=True,
            )

    def _get_feltsti(self, conn) -> str:
        """Looks up the long variable name from the mapping table.

        Reads ``mapping_table`` / ``mapping_match_column`` / ``mapping_result_column``
        so projects whose lookup table uses different column names than the default
        ``mapping_variabelnavn`` (``variabel`` -> ``feltsti``) can configure them
        instead of overriding this method.
        """
        df = conn.table(self.mapping_table)
        result = (
            df.filter(df[self.time_units] == self.period)
            .filter(df[self.mapping_match_column] == self.variable)
            .filter(_.skjema == self.skjema)
            .select(df[self.mapping_result_column])
            .limit(1)
            .execute()
        )
        print(f"Hentet feltsti: {result}")
        if result.empty:
            logger.warning(
                f"No {self.mapping_result_column} found for "
                f"{self.mapping_match_column}='{self.variable}', "
                f"{self.time_units}='{self.period}'. Falling back to kortnavn."
            )
            return self.variable
        return result[self.mapping_result_column].iloc[0]

    def _check_datatype(self, conn) -> str | None:
        """Fetches the expected datatype for `self.variable` and checks whether
        `self.value` could legitimately represent that datatype. Does not modify
        `self.value`. `None` is always considered valid (treated as "no value").

        Returns:
            None if the value is valid for the expected datatype (or is None),
            otherwise the expected datatype string (for use in an error message).
        """
        if self.value is None or self.value == "":
            return None

        t = conn.table("datatyper")
        datatype = (
            t.filter(t[self.time_units] == self.period)
            .filter(_.variabel == self.variable)
            .select(["datatype"])
            .execute()
        )
        datatype = datatype["datatype"].item() if len(datatype) > 0 else None
        if not datatype:
            return None
        print(f"Hentet datatype: {datatype}")
        validator = _VALIDATORS.get(datatype)
        if validator is None:
            logger.warning(
                f"Unknown datatype '{datatype}' for variable '{self.variable}'"
            )
            return datatype
        result = validator(self.value)
        print(f"Hentet validert datatype: {result}")

        if result is True:
            return None
        if result == "float":
            return "float"
        return datatype

    def _insert_ibis(self, conn, long):
        """NØKU-specific function to insert data if the row doesn't exist in the postgreSQL database.
        Because Altinn3-xml only returns data if the values are not None.
        """
        if not isinstance(_get_connection_object(), ConnectionPool):
            logger.error(
                "Insert failed. Not a valid postgreSQL connection. This insert function "
                "only works for tables starting with 'skjemadata', 'kildevalg', or 'saldoskjema'."
            )
            raise PreventUpdate

        if self.table.startswith("skjemadata"):
            feltsti: str = self._get_feltsti(conn)
            columns = {
                f"{self.time_units}": f"'{self.period}'",
                "skjema": f"'{self.skjema}'",
                "ident": f"'{self.ident}'",
                "refnr": f"'{self.refnr}'",
                "feltsti": f"'{feltsti}'",
                "variabel": f"'{self.variable}'",
                "verdi": f"'{self.value}'",
            }

            print(f"columns: {columns}")
            insert_query = f"""
                INSERT INTO core_skjemadata ({', '.join(columns.keys())})
                VALUES ({', '.join(columns.values())})
            """
        elif self.table.startswith("saldoskjema"):
            columns = {
                f"{self.time_units}": f"'{self.period}'",
                "orgnr_foretak": f"'{self.ident}'",
                "variabel": f"'{self.variable}'",
                "verdi": f"'{self.value}'",
            }
            insert_query = f"""
                INSERT INTO saldoskjema ({', '.join(columns.keys())})
                VALUES ({', '.join(columns.values())})
            """
        elif self.table.startswith("enhetsinfo"):
            columns = {
                f"{self.time_units}": f"'{self.period}'",
                "ident": f"'{self.ident}'",
                "foretak": "NULL",
                "enhets_type": "'FRTK'",
                "variabel": f"'{self.variable}'",
                "verdi": f"'{self.value}'",
            }
            insert_query = f"""
                INSERT INTO enhetsinfo ({', '.join(columns.keys())})
                VALUES ({', '.join(columns.values())})
            """
        else:
            logger.error(f"No INSERT logic defined for table '{self.table}'.")
            self.to_alert(long, success=False)
            return False

        try:
            print(f"insert query: {insert_query}")
            conn.raw_sql(insert_query)
            logger.info(
                f"Inserted new row with variabel='{self.variable}' and value='{self.value}' into {self.table}."
            )
            self.to_alert(long, success=True)
            return True
        except Exception as e:
            logger.error(f"INSERT feilet: {e}", exc_info=True)
            self.to_alert(long, success=False)
            return False

    def update_ibis(self, long) -> bool:
        print(self)
        with get_connection() as conn:
            datatype_check = self._check_datatype(conn)
            if datatype_check:
                self.to_alert(long, success=False, datatype=datatype_check)
                return False

        identifier_value = self.refnr if self.identifier_column == "refnr" else self.ident
        print(f"identifier_value: {identifier_value}")
        update_query = f"""
            UPDATE {self.table}
            SET {self.column} = '{self.value}'
            WHERE {self.identifier_column} = '{identifier_value}'
        """

        # guards for non-skjemadata tables like enhetsinfo & saldoskjema
        if self.identifier_column != "refnr" and self.time_units:
            time_filters = " ".join([f"AND {self.time_units} = '{self.period}'"])
            update_query = update_query.strip() + "\n" + time_filters
        if self.table.startswith("enhetsinfo"):
            update_query = update_query.strip() + "\nAND enhets_type = 'FRTK' AND foretak IS NULL"
        
        if long:
            update_query = update_query.strip() + f"\nAND variabel = '{self.variable}'"
        else:
            update_query = update_query.strip() + f"\nAND ident = '{self.ident}'"

        print(f"Trying to run update query: {update_query}")
        try:
            with get_connection() as conn:
                result = conn.raw_sql(update_query)
                if result.rowcount == 0:
                    if self.table.startswith(
                        ("skjemadata", "saldoskjema", "enhetsinfo")
                    ):
                        print(
                            f"UPDATE matched 0 rows for {self.identifier_column}='{self.refnr}', "
                            f"variabel='{self.variable}'. Attempting INSERT."
                        )
                        return self._insert_ibis(conn, long)
                    else:
                        self.to_alert(long, success=False)
                        return False
                print(
                    f"Successfully updated '{self.column}' from '{self.old_value}' to '{self.value}'"
                )
                self.to_alert(long, success=True)
                return True
        except Exception as e:
            logger.error(
                f"Update feilet! Kunne ikke oppdatere {self.refnr} - "
                f"'{self.variable if long else self.column}' til '{self.value}'. Feilmelding:\n{e}",
                exc_info=True,
            )
            self.to_alert(long, success=False)
            return False
