import random

import pandas as pd

from ssb_dash_framework import create_database_engine


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


if __name__ == "__main__":
    DemoDataCreator(create_database_engine("sqlite")).build_demo_database()
