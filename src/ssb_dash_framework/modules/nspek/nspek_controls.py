import random

import pandas as pd

from ssb_dash_framework import ControlFrameworkBase
from ssb_dash_framework import register_control
from .nspek_utils import get_nspek_connection
from .nspek_utils import set_nspek_connection

db_user = "nspek-developers@dapla-group-sa-p-ye.iam"
set_nspek_connection(db_user if db_user else "strukt-naering-developers@dapla-group-sa-p-ye.iam")

class NspekControls(ControlFrameworkBase):
    """
    Control framework som bruker nspek_core-tabellene som datakilde
    """

    def __init__(self, time_units=None, applies_to_subset=None):
        if time_units is None:
            time_units = ["aar"]

        if applies_to_subset is None:
            applies_to_subset = {"aar": [2024]}

        super().__init__(time_units=time_units, applies_to_subset=applies_to_subset)

    def get_current_kontroller(self) -> pd.DataFrame:
        """
        Leser kontroll-definisjoner fra database.

        Returns:
            DataFrame med kontrollmetadata
        """
        with get_nspek_connection() as conn:
            cursor = conn.raw_sql("""
                SELECT
                    aar,
                    tema,
                    kontrollid,
                    /*kategori,*/
                    skildring,
                    /*python_fn,
                    sorteringsvariabel,
                    sortering,*/
                    sist_kjoert
                FROM nspek_core.kontroller
                WHERE aar = 2024
            """)

            rows = cursor.fetchall()
            cols = [c[0] for c in cursor.description]

        df = pd.DataFrame(rows, columns=cols)

        df["sist_kjoert"] = pd.to_datetime(df["sist_kjoert"]).dt.strftime("%d.%m.%Y %H:%M")

        return df   


    def get_current_kontrollutslag(self, specific_control=None) -> pd.DataFrame:
        """
        Leser kontrollutslag fra database.

        Args:
            specific_control: filtrer på kontrollid (valgfritt)

        Returns:
            DataFrame med utslag
        """
        with get_nspek_connection() as conn:

            query = """
                SELECT
                    aar,
                    kontrollid,
                    sekvensnummer,
                    orgnr as ident,
                    utslag,
                    verdi
                FROM nspek_core.kontrollutslag
                WHERE aar = 2024
            """

            if specific_control:
                query += f" AND kontrollid = '{specific_control}' ORDER by abs(verdi) DESC"

            cursor = conn.raw_sql(query)
            rows = cursor.fetchall()
            cols = [c[0] for c in cursor.description]

        return pd.DataFrame(rows, columns=cols)

    def run_control(self, kontrollid: str) -> pd.DataFrame:
        return self.get_current_kontrollutslag(kontrollid)

    def run_all_controls(self) -> dict[str, pd.DataFrame]:
        kontroller = self.get_current_kontroller()

        results = {}

        for kontrollid in kontroller["kontrollid"].unique():
            results[kontrollid] = self.run_control(kontrollid)

        return results

    def update_existing_records(self, control_results):
        return None

    def insert_new_records(self, control_results):
        return None