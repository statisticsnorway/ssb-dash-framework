import logging
from typing import Any

from pydantic import BaseModel

from .alert_handler import create_alert
from .config_tools.connection import _get_connection_object
from .config_tools.connection import get_connection

logger = logging.getLogger(__name__)


class UpdateSkjemamottakKommentar(BaseModel):
    refnr: str
    comment: str

    def __str__(self) -> str:
        return (
            "Update to apply:\n"
            f"  Table   : {self.refnr}\n"
            f"  comment : {self.comment}\n"
        )

    def to_alert(self, success):
        if success:
            return create_alert(
                f"Oppdaterte kommentar for {self.refnr}",
                "success",
                ephemeral=True,
            )
        else:
            return create_alert(
                f"Feilet oppdatering av kommentar for {self.refnr}",
                "danger",
                ephemeral=True,
            )

    def update_eimer(self):
        query = f"""UPDATE skjemamottak SET kommentar = '{self.comment}' WHERE refnr = '{self.refnr}'"""
        logger.debug(f"Running query: {query}")
        try:
            _get_connection_object().query(query)
            logger.info(f"Oppdaterte kommentar for {self.refnr}")
            alert = self.to_alert(success=True)
        except Exception as e:
            logger.error(
                f"Update feilet! Kunne ikke oppdatere kommentar for {self.refnr}. Feilmelding: \n{e}",
                exc_info=True,
            )
            alert = self.to_alert(success=False)
        return alert


class UpdateSkjemadata(BaseModel):
    """Model to centralize logic for updating data.

    Args:
        table (str): Name of the table being updated.
        ident (str): Identity of unit being updated.
        refnr (str): Reference number identifying the row.
        column (str): Column that will be updated.
        variable (str): Variable associated with the column. Note, this is identical to column if the table is not in the long format.
        value (Any): New value to write.
        old_value (Any): Previous value in the database.
        long (bool): Whether the database table is in the long format or not.
    """

    table: str
    ident: str
    refnr: str
    column: str
    variable: str
    value: Any
    old_value: Any
    long: bool

    def __str__(self) -> str:
        return (
            "Update to apply:\n"
            f"  Table     : {self.table}\n"
            f"  Table Type: {'long' if self.long else 'wide'}\n"
            f"  Ident     : {self.ident}"
            f"  RefNr     : {self.refnr}\n"
            f"  Column    : {self.column}\n"
            f"  Variable  : {self.variable}\n"
            f"  Value     : {self.old_value} -> {self.value}"
        )

    def to_alert(self, long, success):
        if success:
            return create_alert(
                f"Refnr '{self.refnr}' oppdatert på variabel '{self.variable if long else self.column}' fra '{self.old_value}' til '{self.value}'",
                "success",
                ephemeral=True,
            )
        else:
            return create_alert(
                f"Feilet oppdatering av refnr '{self.refnr}' på variabel '{self.variable if long else self.column}' fra '{self.old_value}' til '{self.value}'. Se logg for detaljer.",
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

    def update_ibis(self, long):
        query = f"""
            UPDATE {self.table}
            SET {self.column} = '{self.value}'
            WHERE refnr = '{self.refnr}'
        """
        if long:
            query = query + f" AND variabel = '{self.variable}'"
        try:
            with get_connection() as conn:
                conn.raw_sql(query)
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
