import logging
from typing import Any
from typing import Literal

from dash.exceptions import PreventUpdate
from pydantic import BaseModel

from ssb_dash_framework.setup.variableselector import VariableSelector
from ssb_dash_framework.setup.variableselector import VariableSelectorOption
import ibis
from ibis import _

from .alert_handler import create_alert
from .config_tools.connection import _get_connection_object
from .config_tools.connection import get_connection
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


class UpdateSkjemamottak(BaseModel):
    refnr: str
    column: str
    value: str | bool

    def __str__(self) -> str:
        return (
            "Update to apply:\n"
            f"  refnr  : {self.refnr}\n"
            f"  value  : {self.value}\n"
            f"  column : {self.column}\n"
        )

    def to_alert(self, success):
        if success:
            return create_alert(
                f"Oppdaterte {self.column} for {self.refnr} til {self.value}",
                "success",
                ephemeral=True,
            )
        else:
            return create_alert(
                f"Feilet oppdatering av {self.column} for {self.refnr}",
                "danger",
                ephemeral=True,
            )

    def update_eimer(self):
        query = f"""UPDATE skjemamottak SET {self.column} = '{self.value}' WHERE refnr = '{self.refnr}'"""
        logger.debug(f"Running query: {query}")
        try:
            _get_connection_object().query(query)
            logger.info(f"Oppdaterte {self.column} for {self.refnr}")
            alert = self.to_alert(success=True)
        except Exception as e:
            logger.error(
                f"Update feilet! Kunne ikke oppdatere {self.column} for {self.refnr}. Feilmelding: \n{e}",
                exc_info=True,
            )
            alert = self.to_alert(success=False)
        return alert

    def update_ibis(self):
        query = f"""
            UPDATE skjemamottak
            SET {self.column} = '{self.value}'
            WHERE refnr = '{self.refnr}'
        """
        try:
            with get_connection() as conn:
                conn.raw_sql(query)
            logger.info(f"Successfully updated '{self.column}' to '{self.value}'")
            return self.to_alert(success=True)
        except Exception as e:
            logger.error(
                f"Update feilet! Kunne ikke oppdatere {self.refnr} - '{self.column} til '{self.value}'. Feilmelding: \n{e}",
                exc_info=True,
            )
            return self.to_alert(success=False)


class UpdateSkjemamottakStatus(UpdateSkjemamottak):
    value: Literal["Ubehandlet", "Under arbeid", "Ferdig"]
    column: Literal["status"] = "status"


class UpdateSkjemamottakAktiv(UpdateSkjemamottak):
    value: bool
    column: Literal["aktiv"] = "aktiv"


class UpdateSkjemamottakKommentar(UpdateSkjemamottak):
    column: Literal["kommentar"] = "kommentar"


class UpdateSkjemadata(BaseModel):
    f"""Model to centralize logic for updating data.

    Args:
        table (str): Name of the table being updated.
        skjema (str): Type of Altinn3 RA-skjema to insert on.
        ident (str): Identity of unit being updated.
        identifier_column (str): Identifying column to refer to for updates. Usually refnr, ident for non-Altinn3 data.
        refnr (str): Reference number identifying the row.
        time_units (dict): Time units with a dict, 'unit': 'value'. Needed if refnr is missing, to update correct row.
        column (str): Column that will be updated.
        variable (str): Variable associated with the column. Note, this is identical to column if the table is not in the long format.
        value (Any): New value to write.
        old_value (Any): Previous value in the database.
        long (bool): Whether the database table is in the long format or not.
    """

    table: str
    skjema: str | None = None
    ident: str
    identifier_column: str = "refnr"
    refnr: str
    time_units: None | dict = None
    column: str
    variable: str
    value: Any
    old_value: Any
    long: bool

    def __str__(self) -> str:
        return (
            "Update to apply:\n"
            f"  Table             : {self.table}\n"
            f"  Table Type        : {'long' if self.long else 'wide'}\n"
            f"  Ident             : {self.ident}\n"
            f"  Identifier column : {self.identifier_column}\n"
            f"  RefNr             : {self.refnr}\n"
            f"  Time Units        : {self.time_units}\n"
            f"  Column            : {self.column}\n"
            f"  Variable          : {self.variable}\n"
            f"  Value             : {self.old_value} -> {self.value}"
        )

    def to_alert(self, long, success):
        if success:
            return create_alert(
                f"Ident '{self.ident}' oppdatert på variabel '{self.variable if long else self.column}' fra '{self.old_value}' til '{self.value}'",
                "success",
                ephemeral=True,
            )
        else:
            return create_alert(
                f"Feilet oppdatering av ident '{self.ident}' på variabel '{self.variable if long else self.column}' fra '{self.old_value}' til '{self.value}'. Se logg for detaljer.",
                "danger",
                ephemeral=True,
            )

    def update_eimer(self, long):
        query = f"SELECT * FROM {self.table} WHERE refnr = '{self.refnr}'"
        if long:
            query = query + f" AND variabel = '{self.variable}'"
        check = _get_connection_object().query(query)
        logger.debug(f"checking before update using query: {query}\nResults:\n{check}")
        found_old_value = check[self.column].item()
        if not found_old_value == self.old_value:
            raise ValueError(
                f"Old value found  does not match old value provided. Found '{found_old_value}', expected '{self.old_value}'.\nQuery used: {query}"
            )
        logger.info("Updating value")
        if long:
            query = f"""
            UPDATE {self.table}
            SET {self.column} = '{self.value}'
            WHERE refnr = '{self.refnr}'
            AND variabel = '{self.variable}'
            """
        else:
            query = f"""
            UPDATE {self.table}
            SET {self.column} = '{self.value}'
            WHERE refnr = '{self.refnr}'
            """
        try:
            _get_connection_object().query(query)
            logger.info(
                f"Successfully updated '{self.column}' from '{self.old_value}' to '{self.value}'"
            )
            return self.to_alert(long, success=True)
        except Exception as e:
            logger.error(
                f"Update feilet! Kunne ikke oppdatere {self.refnr} - '{self.variable if long else self.column} til '{self.value}'. Feilmelding: \n{e}",
                exc_info=True,
            )
            return self.to_alert(long, success=False)


    def _get_feltsti(self, conn) -> str:
        """Looks up the long variable name from mapping_variabelnavn."""
        df = conn.table("mapping_variabelnavn")
        result = (
            df.filter(_.aar == (self.time_units or {}).get("aar"))
            .filter(_.variabel == self.variable)
            .filter(_.skjema == self.skjema)
            .select(["feltsti"])
            .limit(1)
            .execute()
        )
        if result.empty:
            logger.warning(
                f"No feltsti found for kortnavn='{self.variable}', "
                f"aar='{(self.time_units or {}).get('aar')}'. Falling back to kortnavn."
            )
            return self.variable
        return result["feltsti"].iloc[0]

    def _insert_ibis(self, conn, long):
        """
        NØKU-specific function to insert data if the row doesn't exist in the postgreSQL database.
        Because Altinn3-xml only returns data if the values are not None.
        """

        if not isinstance(_get_connection_object(), ConnectionPool):
            logger.debug("Insert failed. The connection object is not a valid postgreSQL object. This insert function was specifically made for NØKU and only works for tables starting with 'skjemadata', 'kildevalg', or 'saldoskjema'.")
            raise PreventUpdate

        if self.table.startswith("skjemadata"):
            feltsti: str = self._get_feltsti(conn)
            columns = {
                **{unit: f"'{val}'" for unit, val in (self.time_units or {}).items() if val},
                "skjema": f"'{self.skjema}'",
                "ident": f"'{self.ident}'",
                "refnr": f"'{self.refnr}'",
                "feltsti": f"'{feltsti}'",
                "variabel": f"'{self.variable}'",
                "verdi": f"'{self.value}'",
            }
            insert_query = f"""
                INSERT INTO core_skjemadata ({', '.join(columns.keys())})
                VALUES ({', '.join(columns.values())})
            """
        elif self.table.startswith("saldoskjema"):
            columns = {
                **{unit: f"'{val}'" for unit, val in (self.time_units or {}).items() if val},
                "orgnr_foretak": f"'{self.ident}'",
                "variabel": f"'{self.variable}'",
                "verdi": f"'{self.value}'",
            }
            insert_query = f"""
                INSERT INTO saldoskjema ({', '.join(columns.keys())})
                VALUES ({', '.join(columns.values())})
            """

        try:
            conn.raw_sql(insert_query)
            logger.info(f"Inserted new row with variabel='{self.variable}' and value='{self.value}' into {self.table}.")
            return self.to_alert(long, success=True)
        except Exception as e:
            logger.error(f"INSERT feilet: {e}", exc_info=True)
            return self.to_alert(long, success=False)

    def update_ibis(self, long):
        update_query  = f"""
            UPDATE {self.table}
            SET {self.column} = '{self.value}'
            WHERE {self.identifier_column} = '{self.refnr}'
        """
        if self.identifier_column != "refnr" and self.time_units:
            time_filters = " ".join([
                f"AND {unit} = '{val}'" 
                for unit, val in self.time_units.items() 
                if val
            ])
            update_query= update_query.strip() + "\n" + time_filters
        if long:
            update_query= update_query.strip() + f"\nAND variabel = '{self.variable}'"
        else:
            update_query= update_query.strip() + f"\nAND ident = '{self.ident}'"

        try:
            with get_connection() as conn:
                result = conn.raw_sql(update_query)
                if result.rowcount == 0:
                    if self.table.startswith(("skjemadata", "saldoskjema")):
                        logger.warning(
                            f"UPDATE matched 0 rows for {self.identifier_column}='{self.refnr}', "
                            f"variabel='{self.variable}'. Attempting INSERT."
                        )
                        return self._insert_ibis(conn, long)
                    else:
                        return self.to_alert(long, success=False)
                logger.info(
                    f"Successfully updated '{self.column}' from '{self.old_value}' to '{self.value}'"
                )
                return self.to_alert(long, success=True)
        except Exception as e:
            logger.error(
                f"Update feilet! Kunne ikke oppdatere {self.refnr} - '{self.variable if long else self.column} til '{self.value}'. Feilmelding: \n{e}",
                exc_info=True,
            )
            return self.to_alert(long, success=False)
