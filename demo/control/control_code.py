# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -papermill,tags
#     custom_cell_magics: kql
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.2
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---


import eimerdb as db
import pandas as pd

# %% metadata={}
from ssb_dash_framework import ControlFrameworkBase
from ssb_dash_framework import register_control

conn = db.EimerDBInstance(
    "ssb-dapla-felles-data-produkt-prod",
    "produksjonstilskudd_altinn3",
)


class DemoControls(ControlFrameworkBase):
    def __init__(
        self,
        time_units: list[int | str],
        applies_to_subset: dict[str, int | str],
    ) -> None:
        super().__init__(time_units, applies_to_subset)

    @register_control(
        kontrollid="nye",
        kontrolltype="I",
        beskrivelse="Nye enheter for året",
        kontrollerte_variabler=["ident"],
        sorteringsvariabel="fulldyrket",
        sortering="ASC",
    )
    def control_nye(self):
        aar = int(self.applies_to_subset["aar"][0])

        df = conn.query("SELECT * FROM skjemamottak")

        enheter_fjoraar = list(df.loc[df["aar"] == aar - 1]["ident"].unique())

        nye_enheter = df.loc[(df["aar"] == aar) & (~df["ident"].isin(enheter_fjoraar))]
        ikke_nye_enheter = df.loc[
            (df["aar"] == aar) & (df["ident"].isin(enheter_fjoraar))
        ]

        nye_enheter["utslag"] = True
        ikke_nye_enheter["utslag"] = False

        df = pd.concat([nye_enheter, ikke_nye_enheter])
        df["verdi"] = 0

        return df[["aar", "skjema", "ident", "refnr", "utslag", "verdi"]]

    @register_control(
        kontrollid="diff",
        kontrolltype="S",
        beskrivelse="Stor differanse mot fjoråret",
        kontrollerte_variabler=["fulldyrket"],
        sorteringsvariabel="fulldyrket",
        sortering="ASC",
    )
    def control_diff(self):
        aar = int(self.applies_to_subset["aar"][0])
        df = conn.query("SELECT * FROM skjemadata_hoved")
        df = df.loc[df["variabel"] == "fulldyrket"]
        diff_df = df.loc[(df["aar"].isin([aar, aar - 1]))]
        diff_df = diff_df.pivot(
            index=["ident", "variabel"], columns="aar", values="verdi"
        ).reset_index()
        diff_df[aar - 1] = diff_df[aar - 1].astype(float)
        diff_df[aar] = diff_df[aar].astype(float)
        diff_df = diff_df.loc[(diff_df[aar - 1] > 0) & (diff_df[aar] > 0)]

        diff_df["differanse"] = diff_df[aar] - diff_df[aar - 1]
        diff_df["prosent_endring"] = (diff_df["differanse"] / diff_df[aar - 1]) * 100

        diff_df["utslag"] = False
        diff_df.loc[(abs(diff_df["prosent_endring"]) > 100), "utslag"] = True

        diff_df["aar"] = aar
        diff_df["skjema"] = "RA-7357"
        diff_df["kontrollid"] = "diff"
        diff_df["verdi"] = diff_df["prosent_endring"].astype(int)

        diff_df = diff_df.merge(
            df.loc[df["aar"] == aar][["ident", "refnr"]], on="ident"
        )
        return diff_df[
            ["aar", "skjema", "ident", "refnr", "kontrollid", "utslag", "verdi"]
        ]


if __name__ == "__main__":

    test = DemoControls(
        time_units=["aar"],
        applies_to_subset={"aar": 2024, "skjema": "RA-7357"},
        conn=conn,
    )

    test.register_all_controls()
    test.execute_controls()

    print(conn.query("SELECT * FROM kontroller"))

    print(conn.query("SELECT * FROM kontrollutslag"))
