"""This can be used to create a functioning eimerdb instance for your Altinn3 statistic.

It is intended to be a shortcut for quickly getting an editing application up and running, and serve as an example for those making their own setup.

If you'd rather make your own setup, you are free to do so.
"""

import json
import logging

import eimerdb as db

eimerdb_logger = logging.getLogger(__name__)
eimerdb_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
eimerdb_logger.addHandler(handler)
# eimerdb_logger.propagate = False


builder = DatabaseBuilderAltinnEimerdb(
    database_name = "buildertest_kvartal",
    storage_location = "ssb-strukt-naering-data-produkt-prod",
    periods = ["aar", "kvartal"],
)


class DatabaseBuilderAltinnEimerdb:
    """This class provides help for creating an eimerdb datastorage for Altinn3 surveys.

    It provides the recommended tables and provides some functions that can be passed to modules to make the setup process quicker.
    If you want to get the functions for your app

    To use this class for building your storage follow these steps:
    1. Create an instance of the class.
        db_builder = DatabaseHelperAltinnEimerdb(
            database_name = "my-survey-storage",
            storage_location = "path/to/storage",
            periods = "year"
        )
    2. Now that we have our builder ready, check that the schemas are correct.
        print(db_builder.schemas)
    3. Assuming that the schemas are correct, you can now build the eimerdb.
        db_builder.build_storage()
    4. Your database is now done! The only thing that remains is to insert your data into the storage.

    If you are using the suggested schemas without changes, you can use the pre-defined functions for some modules.
        template_funcs = db_builder.get_dashboard_functions()
    """

    def __init__(
        self,
        database_name: str,
        storage_location: str,
        periods: str,
    ) -> None:
        """Initializes the databasebuilder for altinn3 surveys.

        Args:
            database_name:
            storage_location:
            periods: str
        """
        self.database_name = database_name
        self.storage_location = storage_location
        self.periods = periods if isinstance(periods, list) else [periods]
        self._is_valid()

        self.schemas = self._make_schemas()

    def _is_valid(self):
        if not isinstance(self.periods, list):
            raise TypeError("")
        pass

    def _make_schemas(self):
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
                "name": "skjemaversjon",
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
            {"name": "skjemaversjon", "type": "string", "label": "Skjemaets versjon."},
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
            {"name": "skjemaversjon", "type": "string", "label": "Skjemaets versjon."},
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
                "name": "skjemaversjon",
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

    def __str__(self):
        return f"DataStorageBuilderAltinnEimer.\nDatabase name: {self.database_name}\nStorage location: {self.storage_location}\nPeriods variables: {self.periods}\n\nSchemas: {list(self.schemas.keys())}\nDetailed schemas:\n{json.dumps(self.schemas, indent=2, default=str)}"

    def build_storage(self):
        db.create_eimerdb(bucket_name=self.storage_location, db_name=self.database_name)
        conn = db.EimerDBInstance(self.storage_location, self.database_name)
        
        special_tables = {"skjemamottak", "skjemadata_hoved", "kontroller", "kontrollutslag", "kontaktinfo"}
    
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

    def get_dashboard_functions(self):

        return {
            # "EditingTableLong_get_data_func": EditingTableLong_get_data_func,
            # "EditingTableLong_update_table": EditingTableLong_update_table,
        }
