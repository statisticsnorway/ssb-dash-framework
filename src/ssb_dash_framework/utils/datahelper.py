"""These classes can be used to create a functioning database instance for your Altinn3 statistic.

It is intended to be a shortcut for quickly getting an editing application up and running, and serve as an example for those making their own setup.

If you'd rather make your own setup, you are free to do so.

It also contains a utility to fill your database with demo-data.
"""

import json
import logging
import os
import random
from typing import Any

import eimerdb as db
import pandas as pd
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()

logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


class DatabaseBuilderAltinnEimerdb:  # TODO: Should contain functionality to process xml-files into enheter, skjemamottak and kontaktinfo
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

    def _is_valid(self) -> None: ...

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

        schema_col: dict[str, str] = {
            "name": "skjema",
            "type": "string",
            "label": "skjemanummeret",
        }

        schema_skjemamottak = [
            *periods_cols,
            ident_col,
            schema_col,
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
            schema_col,
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
            schema_col,
        ]

        schema_enhetsinfo = [
            *periods_cols,
            ident_col,
            {"name": "variabel", "type": "string", "label": ""},
            {"name": "verdi", "type": "string", "label": ""},
        ]

        schema_kontroller = [
            *periods_cols,
            schema_col,
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
            schema_col,
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

        schema_datatyper = [  # TODO: Should be simplified.
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
            schema_col,
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
        """Returns a string representation of the instance. Shows its planned database name, location, period variables and schemas."""
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
                partition_columns = [*self.periods, "skjema"]
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


PERIOD_COLUMNS = ["aar"]


def period_columns():
    """Generate Column definitions for period dimensions"""
    return {name: Column(String, primary_key=True) for name in PERIOD_COLUMNS}


class Enheter(Base):
    __tablename__ = "enheter"
    locals().update(period_columns())
    ident = Column(String, primary_key=True)
    skjema = Column(String, primary_key=True)


class Enhetsinfo(Base):
    __tablename__ = "enhetsinfo"
    locals().update(period_columns())
    ident = Column(String, primary_key=True)
    variabel = Column(String, primary_key=True)
    verdi = Column(String)


class Skjemamottak(Base):
    __tablename__ = "skjemamottak"
    locals().update(period_columns())
    ident = Column(String, primary_key=True)
    skjema = Column(String, primary_key=True)
    refnr = Column(String, primary_key=True)
    dato_mottatt = Column(String)
    editert = Column(Boolean)
    kommentar = Column(String)
    aktiv = Column(Boolean)

    __table_args__ = (
        ForeignKeyConstraint(
            ["aar", "ident", "skjema"],
            ["enheter.aar", "enheter.ident", "enheter.skjema"],
        ),
    )


class Kontaktinfo(Base):
    __tablename__ = "kontaktinfo"
    locals().update(period_columns())
    ident = Column(String, primary_key=True)
    skjema = Column(String, primary_key=True)
    refnr = Column(String, primary_key=True)
    kontaktperson = Column(String, nullable=True)
    epost = Column(String, nullable=True)
    telefon = Column(String, nullable=True)
    bekreftet_kontaktinfo = Column(String, nullable=True)
    kommentar_kontaktinfo = Column(String, nullable=True)
    kommentar_krevende = Column(String, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["aar", "ident", "skjema"],
            ["enheter.aar", "enheter.ident", "enheter.skjema"],
        ),
        ForeignKeyConstraint(
            ["aar", "ident", "skjema", "refnr"],
            [
                "skjemamottak.aar",
                "skjemamottak.ident",
                "skjemamottak.skjema",
                "skjemamottak.refnr",
            ],
        ),
    )


class Kontroller(Base):
    __tablename__ = "kontroller"
    locals().update(period_columns())
    skjema = Column(String, primary_key=True)
    kontrollid = Column(String, primary_key=True)
    kontrolltype = Column(String)
    skildring = Column(String)
    kontrollvariabel = Column(String)
    sorteringsvariabel = Column(String)


class Kontrollutslag(Base):
    __tablename__ = "kontrollutslag"
    locals().update(period_columns())
    kontrollid = Column(String, primary_key=True)
    skjema = Column(String, primary_key=True)
    ident = Column(String, primary_key=True)
    refnr = Column(String, primary_key=True)
    utslag = Column(Boolean)
    verdi = Column(Integer)  # Maybe other type?

    __table_args__ = (
        ForeignKeyConstraint(
            ["skjema", "kontrollid"], ["kontroller.skjema", "kontroller.kontrollid"]
        ),
        ForeignKeyConstraint(
            ["aar", "ident", "skjema"],
            ["enheter.aar", "enheter.ident", "enheter.skjema"],
        ),
        ForeignKeyConstraint(
            ["aar", "ident", "skjema", "refnr"],
            [
                "skjemamottak.aar",
                "skjemamottak.ident",
                "skjemamottak.skjema",
                "skjemamottak.refnr",
            ],
        ),
    )


class Skjemadata_hoved(Base):
    __tablename__ = "skjemadata_hoved"
    locals().update(period_columns())
    skjema = Column(String, primary_key=True)
    ident = Column(String, primary_key=True)
    refnr = Column(String, primary_key=True)
    variabel = Column(String, primary_key=True)
    verdi = Column(String)

    __table_args__ = (
        ForeignKeyConstraint(
            ["aar", "ident", "skjema", "refnr"],
            [
                "skjemamottak.aar",
                "skjemamottak.ident",
                "skjemamottak.skjema",
                "skjemamottak.refnr",
            ],
        ),
    )


class Datatyper(Base):
    __tablename__ = "datatyper"
    locals().update(period_columns())
    variabel = Column(String)
    datatype = Column(String)
    tabell = Column(String)
    radnr = Column(String)


def create_database_engine(database_type, *args, **kwargs):
    if database_type == "sqlite":
        engine = create_engine(
            f"sqlite:///{kwargs.get('sqlite_path', 'mydb.sqlite')}", echo=True
        )
    elif database_type == "postgres":
        user = os.environ.get("DB_USER", "dev")
        password = os.environ.get("DB_PASSWORD", "")
        host = os.environ.get("DB_HOST", "localhost")
        port = os.environ.get("DB_PORT", "5432")
        db = os.environ.get("DB_NAME", "devdb")
        if password:
            conn_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
        else:
            conn_str = f"postgresql+psycopg2://{user}@{host}:{port}/{db}"
        engine = create_engine(conn_str, echo=True)
    else:
        raise ValueError(f"Unsupported database type: {database_type}")
    return engine


def create_database(engine):
    Base.metadata.create_all(engine)


class DemoDataCreator:
    def __init__(self, engine) -> None:
        self.engine = engine

    def build_demo_database(self):
        self.get_data()
        self.get_enheter()
        self.get_skjemamottak()
        self.get_skjemadata_hoved()
        self.get_kontaktinfo()
        self.get_enhetsinfo()

    def random_date(self):
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        return f"{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

    def insert_to_db(self, table_name, dataframe):
        dataframe.to_sql(table_name, self.engine, if_exists="replace", index=False)

    def get_data(self):
        df = pd.DataFrame()
        for i in range(2017, 2026):
            df = pd.concat(
                [
                    df,
                    pd.read_csv(
                        f"https://raw.githubusercontent.com/LandbruksdirektoratetGIT/opendata/refs/heads/main/datasets/produksjon-og-avlosertilskudd/{i}/dataset.csv",
                        sep=";",
                    ),
                ]
            )

        df = df.rename({"orgnr": "ident", "soeknads_aar": "aar"}, axis=1)
        df["ident"] = df["ident"].astype(str)
        df["skjema"] = "RA-7357"
        df["refnr"] = df.index.astype(str)
        self.data = df

    def get_enheter(self):
        enheter = self.data.copy()
        enheter = enheter[["ident", "aar"]]
        enheter["skjema"] = "RA-7357"
        enheter = enheter[["ident", "skjema", "aar"]]
        self.insert_to_db("enheter", enheter)

    def get_skjemamottak(self):
        skjemamottak = self.data.copy()
        skjemamottak["dato"] = skjemamottak.apply(
            lambda row: self.random_date(), axis=1
        )
        skjemamottak["dato_mottatt"] = (
            skjemamottak["aar"].astype(str) + "-" + skjemamottak["dato"]
        )
        skjemamottak["dato_mottatt"] = pd.to_datetime(skjemamottak["dato_mottatt"])
        skjemamottak["dato_mottatt"] = skjemamottak["dato_mottatt"].dt.floor("s")
        skjemamottak["editert"] = False
        skjemamottak["kommentar"] = ""
        skjemamottak["aktiv"] = True
        skjemamottak = skjemamottak[
            [
                "aar",
                "ident",
                "skjema",
                "refnr",
                "dato_mottatt",
                "editert",
                "kommentar",
                "aktiv",
            ]
        ]
        self.insert_to_db("skjemamottak", skjemamottak)

    def get_skjemadata_hoved(self):
        skjemadata_lang = self.data.copy()

        skjemadata_lang = skjemadata_lang.melt(
            id_vars=["aar", "skjema", "ident", "refnr"],
            value_vars=[
                "beitetilskudd",
                "totalareal",
                "utmarksbeitetilskudd",
                "fulldyrket",
                "overflatedyrket",
                "husdyrtilskudd",
                "innmarksbeite",
                "arealtilskudd",
                "kulturlandskapstilskudd",
                "bunnfradrag",
                "avloesertilskudd",
                "oekologiskhusdyrtilskudd",
                "smaa_mellomstore_melkebruk",
                "bevaringsverdige_husdyr_tilsku",
                "oekologiskarealtilskudd",
                "tilskudd_bevaringsverdige_husdyrraser",
                "storfekjoettproduksjon",
                "distriktstilskudd_frukt_baer_veksthusgronnsaker",
                "distriktstilskudd_matpotet_nordnorge",
                "distriktstilskudd_frukt_groent",
                "distriktstilskudd_potet",
                "melkeproduksjon",
                "avlosertilskudd_ferie_fritid",
                "driftstilskudd_melkeproduksjon",
                "okologisk_arealtilskudd",
                "distriktstilskudd_potet_gronns",
                "okologisk_husdyrtilskudd",
                "driftstilskudd_ spesialisert_storfekjottproduksjon",
            ],
            var_name="variabel",
            value_name="verdi",
        )

        skjemadata_lang = skjemadata_lang.loc[skjemadata_lang["verdi"].fillna(0) > 0]
        skjemadata_lang["verdi"] = skjemadata_lang["verdi"].astype(str)
        self.insert_to_db("skjemadata_hoved", skjemadata_lang)

    def get_enhetsinfo(self):
        enhetsinfo = self.data.melt(
            id_vars=[
                "aar",
                "ident",
            ],
            value_vars=[
                "orgnavn",
                "kommunenr",
                "gaardsnummer",
                "bruksnummer",
                "festenummer",
            ],
            var_name="variabel",
            value_name="verdi",
        )
        enhetsinfo["verdi"] = enhetsinfo["verdi"].astype(str)
        self.insert_to_db("enhetsinfo", enhetsinfo)

    def get_kontaktinfo(self):
        kontaktinfo = self.data.copy()
        kontaktinfo = kontaktinfo[["aar", "skjema", "ident", "refnr"]]
        kontaktinfo[
            [
                "kontaktperson",
                "epost",
                "telefon",
                "bekreftet_kontaktinfo",
                "kommentar_kontaktinfo",
                "kommentar_krevende",
            ]
        ] = ("", "", "", "", "", "")
        self.insert_to_db("kontaktinfo", kontaktinfo)
