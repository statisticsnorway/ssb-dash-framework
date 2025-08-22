"""This can be used to create a functioning eimerdb instance for your Altinn3 statistic.

It is intended to be a shortcut for quickly getting an editing application up and running, and serve as an example for those making their own setup.

If you'd rather make your own setup, you are free to do so.
"""

import json
import logging
from typing import Any

import eimerdb as db

eimerdb_logger = logging.getLogger(__name__)
eimerdb_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
eimerdb_logger.addHandler(handler)
eimerdb_logger.propagate = False


class DatabaseBuilderAltinnEimerdb:
    """This class provides help for creating an eimerdb datastorage for Altinn3 surveys.

    It provides the recommended tables which makes sure your datastructure is compatible with the framework.

    To use this class for building your storage follow these steps:
    1. Create an instance of the class.
        db_builder = DatabaseBuilderAltinnEimerdb(
            database_name = "my-database-name",
            storage_location = "path/to/storage",
            periods = "year" # can be list for more time identifiers
        )
    2. Now that we have our builder ready, check that the schemas are correct.
        print(db_builder.schemas)
    3. Assuming that the schemas are correct, you can now build the eimerdb.
        db_builder.build_storage()
    4. Your database is now done! The only thing that remains is to insert your data into the storage.

    Note:
        You can add your own custom 'skjemadata' tables if you so wish, just make sure their names start with 'skjemadata_'.
        It is possible to use this functionality to create your data storage even if your data are not from Altinn, but you might need to adapt your data.
    """

    def __init__(
        self,
        database_name: str,
        storage_location: str,
        periods: str | list[str],
    ) -> None:
        """Initializes the databasebuilder for altinn3 surveys.

        Args:
            database_name: The name you want for your eimerdb database.
            storage_location: The path to the bucket for your database.
            periods: String or list of strings containing your period variables (such as 'year', 'quarter', 'month').
        """
        self.database_name = database_name
        self.storage_location = storage_location
        self.periods = periods if isinstance(periods, list) else [periods]
        self._is_valid()

        self.schemas = self._make_schemas()

    def _is_valid(self) -> None:
        ...

    def _make_schemas(self) -> dict[str, list[Any]]:
        periods_cols = [
            {"name": period, "type": "int64", "label": period}
            for period in self.periods
        ]
        ident_col = {
            "name": "ident",
            "type": "string",
            "label": "Identnummeret.",
        }

        schema_col = {"name": "skjema", "type": "string", "label": "Skjema"}

        schema_skjemamottak = [
            *periods_cols,
            ident_col,
            {
                "name": "skjema",
                "type": "string",
                "label": "Skjemaet.",
                "app_editable": False,
            },
            {
                "name": "refnr",
                "type": "string",
                "label": "Skjemaets versjon.",
                "app_editable": False,
            },
            {
                "name": "dato_mottatt",
                "type": "pa.timestamp(s)",
                "label": "Datoen og tidspunktet for når skjemaet ble mottatt.",
                "app_editable": False,
            },
            {
                "name": "editert",
                "type": "bool_",
                "label": "Editeringskode. True = Editert. False = Ueditert.",
                "app_editable": True,
            },
            {
                "name": "kommentar",
                "type": "string",
                "label": "Editeringskommentar.",
                "app_editable": True,
            },
            {
                "name": "aktiv",
                "type": "bool_",
                "label": "1 hvis skjemaet er aktivt. 0 hvis skjemaet er satt til inaktivt.",
                "app_editable": True,
            },
        ]

        schema_kontaktinfo = [
            *periods_cols,
            ident_col,
            {"name": "skjema", "type": "string", "label": "skjemanummeret"},
            {"name": "refnr", "type": "string", "label": "Skjemaets versjon."},
            {"name": "kontaktperson", "type": "string", "label": "Kontaktperson."},
            {"name": "epost", "type": "string", "label": "epost."},
            {"name": "telefon", "type": "string", "label": "telefon."},
            {
                "name": "bekreftet_kontaktinfo",
                "type": "string",
                "label": "Om kontaktinformasjonen er bekreftet.",
            },
            {
                "name": "kommentar_kontaktinfo",
                "type": "string",
                "label": "Kommentar til kontaktinfo.",
            },
            {
                "name": "kommentar_krevende",
                "type": "string",
                "label": "En kommentar rundt hva respondenten opplevde som krevende.",
            },
        ]

        schema_enheter = [
            *periods_cols,
            ident_col,
            {
                "name": "skjemaer",
                "type": "string",
                "label": "En liste over skjemaene enheten har mottatt.",
            },
        ]

        schema_enhetsinfo = [
            *periods_cols,
            ident_col,
            {"name": "variabel", "type": "string", "label": ""},
            {"name": "verdi", "type": "string", "label": ""},
        ]

        schema_kontroller = [
            *periods_cols,
            {"name": "skjema", "type": "string", "label": "skjemanummeret"},
            {"name": "kontrollid", "type": "string", "label": "kontrollens unike ID."},
            {
                "name": "type",
                "type": "string",
                "label": "Kontrolltypen. Sum eller tall.",
            },
            {
                "name": "skildring",
                "type": "string",
                "label": "En skildring av kontrollen.",
            },
            {
                "name": "kontrollvar",
                "type": "string",
                "label": "Navnet på variabelen som ligger i hvert kontrollutslag.",
            },
            {
                "name": "varsort",
                "type": "string",
                "label": "Sorteringslogikken til kontrollvariabelen. ASC eller DESC.",
            },
        ]

        schema_kontrollutslag = [
            *periods_cols,
            {"name": "skjema", "type": "string", "label": "skjemanummeret"},
            ident_col,
            {"name": "refnr", "type": "string", "label": "Skjemaets versjon."},
            {"name": "kontrollid", "type": "string", "label": "kontrollens unike ID."},
            {
                "name": "utslag",
                "type": "bool_",
                "label": "Om kontrollen slår ut på enheten eller ikke.",
            },
            {
                "name": "verdi",
                "type": "int32",
                "label": "Verdien til den utvalgte sorteringsvariabelen til utslagene.",
            },
        ]

        schema_datatyper = [
            *periods_cols,
            {"name": "tabell", "type": "string", "label": "Tabellnavnet"},
            {
                "name": "radnr",
                "type": "int16",
                "label": "Radnummer. Viser rekkefølgen på variabelene.",
            },
            {"name": "variabel", "type": "string", "label": "Variabelen."},
            {"name": "datatype", "type": "string", "label": "Datatypen til variabelen"},
            {
                "name": "skildring",
                "type": "string",
                "label": "En skildring av variabelen",
            },
        ]

        schema_skjemadata_hoved = [
            *periods_cols,
            {
                "name": "skjema",
                "type": "string",
                "label": "skjemaet tilh\u00f8rende skjemadataene.",
                "app_editable": False,
            },
            ident_col,
            {
                "name": "refnr",
                "type": "string",
                "label": "Skjemaets versjon.",
                "app_editable": False,
            },
            {
                "name": "variabel",
                "type": "string",
                "label": "variabel",
                "app_editable": False,
            },
            {
                "name": "verdi",
                "type": "string",
                "label": "verdien til variabelen.",
                "app_editable": True,
            },
        ]

        return {
            "skjemamottak": schema_skjemamottak,
            "kontaktinfo": schema_kontaktinfo,
            "enheter": schema_enheter,
            "enhetsinfo": schema_enhetsinfo,
            "kontroller": schema_kontroller,
            "kontrollutslag": schema_kontrollutslag,
            "datatyper": schema_datatyper,
            "skjemadata_hoved": schema_skjemadata_hoved,
        }

    def __str__(self) -> str:
        return f"DataStorageBuilderAltinnEimer.\nDatabase name: {self.database_name}\nStorage location: {self.storage_location}\nPeriods variables: {self.periods}\n\nSchemas: {list(self.schemas.keys())}\nDetailed schemas:\n{json.dumps(self.schemas, indent=2, default=str)}"

    def build_storage(self) -> None:
        """Calling this method builds your eimerdb storage with the supplied name at the specified location and creates partitions for the defined periods."""
        db.create_eimerdb(bucket_name=self.storage_location, db_name=self.database_name)
        conn = db.EimerDBInstance(self.storage_location, self.database_name)

        special_tables = {
            "skjemamottak",
            "skjemadata_hoved",
            "kontroller",
            "kontrollutslag",
            "kontaktinfo",
        }

        for table in self.schemas:
            if table in special_tables:
                partition_columns = self.periods + ["skjema"]
            else:
                partition_columns = self.periods

            conn.create_table(
                table_name=table,
                schema=self.schemas[table],
                partition_columns=partition_columns,
                editable=True,
            )
        eimerdb_logger.info(
            f"Created eimerdb at {self.storage_location}.\nAs the next step, insert data into enheter, skjemamottak and skjemadata to get started. \nSchemas: {list(self.schemas.keys())}\nDetailed schemas:\n{json.dumps(self.schemas, indent=2, default=str)}"
        )
