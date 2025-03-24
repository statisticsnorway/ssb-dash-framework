"""This can be used to create a functioning eimerdb instance for your statistic.

It is intended to be a shortcut for quickly getting an editing application online and serve as an example for those making their own setup.

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


class DatabaseBuilderAltinnEimerdb:
    """This class provides help for creating an eimerdb datastorage for Altinn3 surveys.

    It provides the recommended tables and provides some functions that can be passed to modules to make the setup process quicker.
    If you want to get the functions for your app

    To use this class for building your storage follow these steps:
    1. Create an instance of the class.
        db_builder = DatabaseHelperAltinnEimerdb(
            database_name = "my-survey-storage",
            storage_location = "path/to/storage",
            period = "year"
        )
    2. Now that we have our builder ready, check that the schemas are correct.
        print(db_builder.schemas)
    3. Assuming that the schemas are correct, you can now build the eimerdb.
        db_builder.build_storage()
    4. Your database is now done! The only thing that remains is to insert your data into the storage.

    If you are using the suggested schemas without changes, you can use the pre-defined functions for some modules.
        template_funcs = db_builder.get_dashboard_functions()
    """

    def __init__(self, database_name: str, storage_location: str, period: str) -> None:
        """Initializes the databasebuilder for altinn3 surveys.

        Args:
            database_name:
            storage_location:
            period: str
        """
        self.period = period
        self.storage_location = storage_location
        self.database_name = database_name

        self._is_valid()

        self.schemas = self._make_schemas()

    def _is_valid(self):
        pass

    def _make_schemas(self):
        period_col = {"name": self.period, "type": "int64", "label": self.period}
        ident_col = {
            "name": "enhetsident",
            "type": "string",
            "label": "Oppgavegiver sin id.",
        }
        name_col = {"name": "orgnr", "type": "string", "label": "Organisasjonsnummer"}
        delivery_id_col = {
            "name": "referanse",
            "type": "string",
            "label": "Altinn referanse.",
        }
        skjema_col = {"name": "skjema", "type": "string", "label": "Skjema"}

        schema_enheter = [
            period_col,
            skjema_col,
            name_col,
            ident_col,
        ]

        schema_enhetsinfo = [
            period_col,
            ident_col,
            {"name": "opplysning", "type": "string", "label": "Opplysning"},
            {"name": "opplysningsverdi", "type": "string", "label": "Opplysningsverdi"},
        ]

        schema_skjemamottak = [
            period_col,
            ident_col,
            skjema_col,
            delivery_id_col,
            {"name": "leveringstid", "type": "string", "label": "Altinn leveringstid."},
            {"name": "editert", "type": "bool_", "label": "Editeringsstatus"},
            {"name": "kommentar", "type": "string", "label": "Intern kommentar"},
            {"name": "aktiv", "type": "string", "label": "Aktiv"},
        ]

        schema_kontaktinfo = [
            period_col,
            ident_col,
            skjema_col,
            delivery_id_col,
            {"name": "kontaktperson", "type": "string", "label": "Kontaktperson"},
            {"name": "epost", "type": "string", "label": "Epost adresse"},
            {"name": "telefon", "type": "string", "label": "Telefonnummer"},
            {"name": "kommentar", "type": "string", "label": "Kommentar"},
            {
                "name": "kommentar_krevende",
                "type": "string",
                "label": "Kommentar_krevende",
            },
        ]

        schema_skjemadata = [
            period_col,
            skjema_col,
            delivery_id_col,
            {"name": "variabelnavn", "type": "string", "label": "Variabelens navn"},
            {"name": "variabelverdi", "type": "string", "label": "Variabelens verdi."},
        ]

        schema_kontroller = [
            period_col,
            skjema_col,
            {"name": "kontrollutslagid", "type": "string", "label": "Kontrollutslagid"},
            {"name": "kontrolltype", "type": "string", "label": "Kontrolltype"},
            {
                "name": "kontrollvar",
                "type": "string",
                "label": "Kontrollvariabel for sortering",
            },
            {"name": "sort", "type": "string", "label": "Sorting (ASC / DESC)"},
        ]

        schema_kontrollutslag = [
            period_col,
            skjema_col,
            ident_col,
            delivery_id_col,
            {"name": "kontrollutslagid", "type": "string", "label": "Kontrollutslagid"},
            {"name": "editert", "type": "string", "label": "Editeringsstatus"},
            {"name": "utslag", "type": "string", "label": "Utslag"},
            {"name": "verdi", "type": "string", "label": "Utslagsverdi"},
        ]

        return {
            "enheter": schema_enheter,
            "enhetsinfo": schema_enhetsinfo,
            "skjemamottak": schema_skjemamottak,
            "kontaktinfo": schema_kontaktinfo,
            "skjemadata": schema_skjemadata,
            "kontroller": schema_kontroller,
            "kontrollutslag": schema_kontrollutslag,
        }

    def __str__(self):
        return f"DataStorageBuilderAltinnEimer.\nDatabase name: {self.database_name}\nPeriod variable: {self.period}\nStorage location: {self.storage_location}\n\nSchemas: {list(self.schemas.keys())}\nDetailed schemas:\n{json.dumps(self.schemas, indent=2, default=str)}"

    def build_storage(self):
        db.create_eimerdb(bucket_name=self.storage_location, db_name=self.database_name)
        conn = db.EimerDBInstance(self.storage_location, self.database_name)
        for table in self.schemas:
            conn.create_table(
                table_name=table,
                schema=self.schemas[table],
                partition_columns=(
                    [self.period, "skjema"]
                    if table not in ["enhetsinfo"]
                    else [self.period]
                ),
                editable=True,
            )
        eimerdb_logger.info(
            f"Created eimerdb at {self.storage_location}.\nAs the next step, insert data into enheter, skjemamottak and skjemadata to get started. \nSchemas: {list(self.schemas.keys())}\nDetailed schemas:\n{json.dumps(self.schemas, indent=2, default=str)}"
        )

    def get_dashboard_functions(self):

        def EditingTableLong_get_data_func(
            database, tabell, *args
        ):  # Need to make partition_select dynamic?
            orgnr, delreg, *other_args = args
            orgnr = database.query(
                f"""SELECT enhetsident FROM enheter WHERE orgnr = '{orgnr}'""",
                partition_select={"delreg": [delreg]},
            ).iloc[0, 0]
            leveranser = database.query(
                f"""SELECT * FROM skjemamottak WHERE enhetsident = '{orgnr}'""",
                partition_select={"delreg": [delreg]},
            )["referanse"].unique()
            aktuelt_skjema = leveranser[0]
            skjemadata = database.query(
                f"""SELECT row_id, variabelnavn, variabelverdi FROM skjemadata WHERE referanse = '{aktuelt_skjema}'"""
            )
            return skjemadata

        def EditingTableLong_update_table(database, tabell, variable, value, row_id):
            database.query(
                f"""UPDATE {tabell}
                SET {variable} = {value}
                WHERE row_id = '{row_id}'
                """,
            )

        return {
            "EditingTableLong_get_data_func": EditingTableLong_get_data_func,
            "EditingTableLong_update_table": EditingTableLong_update_table,
        }
