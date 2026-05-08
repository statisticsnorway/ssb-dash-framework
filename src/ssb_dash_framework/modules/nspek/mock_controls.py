import random

import pandas as pd

from ssb_dash_framework import ControlFrameworkBase
from ssb_dash_framework import register_control

ORGNRS = [
    "979443137",
    "933942333",
    "984600526",
    "926500473",
    "982734444",
    "922133069",
    "813735512",
    "813769662",
    "813753642",
]


class NspekMockControls(ControlFrameworkBase):

    def __init__(self, time_units=None, applies_to_subset=None):
        if time_units is None:
            time_units = ["aar"]

        if applies_to_subset is None:
            applies_to_subset = {"aar": [2024]}

        super().__init__(time_units=time_units, applies_to_subset=applies_to_subset)

    def get_current_kontroller(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "aar": 2024,
                    "tema": "Resultat",
                    "kontrollid": "K001",
                    "kategori": "H",
                    "skildring": "Negative verdier",
                    "python_fn": "control_negative_values",
                    "sorteringsvariabel": "verdi",
                    "sortering": "DESC",
                },
                {
                    "aar": 2024,
                    "tema": "Balanse",
                    "kontrollid": "K002",
                    "kategori": "S",
                    "skildring": "Balanseavvik",
                    "python_fn": "control_balanse",
                    "sorteringsvariabel": "verdi",
                    "sortering": "DESC",
                },
                {
                    "aar": 2024,
                    "tema": "Resultat",
                    "kontrollid": "K003",
                    "kategori": "H",
                    "skildring": "Resultatavvik",
                    "python_fn": "control_resultat",
                    "sorteringsvariabel": "verdi",
                    "sortering": "DESC",
                },
            ]
        )

    def get_current_kontrollutslag(self, specific_control=None) -> pd.DataFrame:

        rows = []

        for kontrollid in ["K001", "K002", "K003"]:
            for i, orgnr in enumerate(ORGNRS, start=1):
                rows.append(
                    {
                        "aar": 2024,
                        "kontrollid": kontrollid,
                        "ident": orgnr,
                        "refnr": i,
                        "utslag": random.choice([True, False]),
                        "verdi": random.randint(0, 1000),
                    }
                )

        df = pd.DataFrame(rows)

        if specific_control:
            df = df[df["kontrollid"] == specific_control]

        return df

    @register_control(
        kontrollid="K001",
        kontrolltype="H",
        beskrivelse="Negative verdier",
        kontrollerte_variabler=["verdi"],
        sorteringsvariabel="verdi",
        sortering="DESC",
    )
    def control_negative_values(self):

        rows = []

        for i, orgnr in enumerate(ORGNRS, start=1):
            value = random.randint(-500, 500)

            rows.append(
                {
                    "aar": 2024,
                    "kontrollid": "K001",
                    "ident": orgnr,
                    "refnr": i,
                    "utslag": value < 0,
                    "verdi": value,
                }
            )

        return pd.DataFrame(rows)

    @register_control(
        kontrollid="K002",
        kontrolltype="S",
        beskrivelse="Balanseavvik",
        kontrollerte_variabler=["balanse"],
        sorteringsvariabel="verdi",
        sortering="DESC",
    )
    def control_balanse(self):

        rows = []

        for i, orgnr in enumerate(ORGNRS, start=1):
            value = random.randint(0, 2000)

            rows.append(
                {
                    "aar": 2024,
                    "kontrollid": "K002",
                    "ident": orgnr,
                    "refnr": i,
                    "utslag": value > 1000,
                    "verdi": value,
                }
            )

        return pd.DataFrame(rows)

    @register_control(
        kontrollid="K003",
        kontrolltype="H",
        beskrivelse="Resultatavvik",
        kontrollerte_variabler=["resultat"],
        sorteringsvariabel="verdi",
        sortering="DESC",
    )
    def control_resultat(self):

        rows = []

        for i, orgnr in enumerate(ORGNRS, start=1):
            value = random.randint(0, 500)

            rows.append(
                {
                    "aar": 2024,
                    "kontrollid": "K003",
                    "ident": orgnr,
                    "refnr": i,
                    "utslag": value == 0,
                    "verdi": value,
                }
            )

        return pd.DataFrame(rows)

    # -------------------------------------------------
    # 🔧 DEV MODE (slå av DB-sync)
    # -------------------------------------------------
    def update_existing_records(self, control_results):
        return None

    def insert_new_records(self, control_results):
        return None
