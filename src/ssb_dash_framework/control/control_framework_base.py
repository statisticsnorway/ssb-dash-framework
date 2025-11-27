import itertools
import logging
import warnings
from typing import Any

import ibis
import pandas as pd
from eimerdb import EimerDBInstance
from ibis import _

# from .utils.core_query_functions import conn_is_ibis, ibis_filter_with_dict


logger = logging.getLogger(__name__)


def conn_is_ibis(conn: Any) -> bool:
    """Function to check if a supplied object is an Ibis connection.

    Used to select which 'path' to take for preparing data in modules.

    Args:
        conn (Any): Object to check.

    Returns:
        A bool that is True if the supplied object is an Ibis connection.
    """
    if conn.__class__.__name__ == "Backend":
        logger.debug("Assuming 'self.conn' is Ibis connection.")
        return True
    else:
        return False


def create_filter_dict(variables: list[str], values: list[Any] | tuple[Any]):
    """Creates a filter dict for use in ibis_filter_with_dict."""
    return dict(zip(variables, values, strict=False))


def ibis_filter_with_dict(periods_dict):
    """Example:
    filter_dict = {"year": "2025", "quarter": ["3", "4"]}
    t.filter(ibis_filter_with_dict(filter_dict))
    """
    filters = []
    for key, value in periods_dict.items():
        col = getattr(_, key)
        if isinstance(value, list):
            expr = col.isin(value)
        else:
            expr = col == value
        filters.append(expr)
    return filters


def control(
    kontrollid, kontrolltype, skildring, kontrollvariabel, sorteringsvariabel, **kwargs
):
    """Decorator used to attach REQUIRED metadata to control_<id> methods.

    Required fields:
        - kontrollid
        - type
        - skildring
        - kontrollvar
        - varsort
    """
    required_keys = {
        "kontrollid",
        "type",
        "skildring",
        "kontrollvar",  # Optional?
        "varsort",  # Optional?
    }
    meta_dict = {
        "kontrollid": kontrollid,
        "type": kontrolltype,
        "skildring": skildring,
        "kontrollvar": kontrollvariabel,
        "varsort": sorteringsvariabel,
    }

    # Check for missing required keys
    for required in required_keys:
        if required not in meta_dict.keys():
            raise ValueError(f"This definition is missing required field '{required}'.")

    def wrapper(func):
        func._control_meta = meta_dict
        return func

    return wrapper


class ControlFrameworkBase:  # TODO: Add some common control methods here for easier reuse.
    """Base class for running control checks.

    Designed to work on partitioned data following the recommended altinn3 data structure. Manages inserts and updates
    to the 'kontrollutslag' table via a connection interface.

    To use this class you need to use this setup:
    class MyControls(ControlFrameworkBase):
        def __init__(self, partitions: list[int | str], partitions_skjema: dict[str, int | str], conn: object) -> None:
            super().__init__(partitions, partitions_skjema, conn)

        def a_control_func(self):
            # Your code here
            return dataframe


    The flow of updating the control table works like this:

        1. First call 'execute_controls', this begins the entire process.
        2. 'control_updates' is run, during which the code checks existing controls, runs all controls and creates a dataframe with all results.
            'run_all_controls' is run, which in turn calls 'run_control' for each individual control.
            The results from control_updates is used to check if there has been any changes since last executing controls. If there are no changes, the process stops here.
        3. Based on the results from 'control_updates' it generates an update query where each change in the results, where the result of a control has changed for an observation, is updated in the 'kontrollutslag' table.
        4. The update query is run, and the process is complete.
    """

    _required_kontroller_columns = [
        "kontrollid",
        "kontrolltype",
        "skildring",
    ]

    _required_kontrollutslag_columns = [
        "kontrollid",
        "ident",
        "refnr",
        "utslag",
    ]

    def __init__(
        self,
        time_units: list[str],
        applies_to_subset: dict[str, Any],
        conn: object,
        partitions: list[int | str] | None = None,  # Deprecated name
        partitions_skjema: dict[str, int | str] | None = None,  # Deprecated name
    ) -> None:
        """Initialize the control framework.

        Args:
            partitions: Partition to execute controls on.
            partitions_skjema: Partition specification, including skjema.
            conn: Database connection object.

        Raises:
            AttributeError: If conn lacks 'query' or 'insert' methods.
            ValueError: if no controls are found for chosen partition.
        """
        if partitions is not None or partitions_skjema is not None:
            warnings.warn(
                "The 'partitions' and 'partitions_skjema' parameters are deprecated. "
                "Use 'time_units' and 'valid_for' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if time_units is None:
                time_units = partitions
            if applies_to_subset is None:
                # Needs transformation here
                applies_to_subset = partitions_skjema
        self.time_units = time_units
        self.applies_to_subset = applies_to_subset
        self.conn = conn

        self._required_kontroller_columns = [
            *self.time_units,
            *ControlFrameworkBase._required_kontroller_columns,
        ]
        self._required_kontrollutslag_columns = [
            *self.time_units,
            *ControlFrameworkBase._required_kontrollutslag_columns,
        ]

    def find_control_methods(self):
        self.controls = []
        for method_name in dir(self):
            if hasattr(getattr(test, method_name), "_control_meta"):
                self.controls.append(method_name)
        if len(self.controls) == 0:
            raise ValueError("No control methods found.")
        print(self.controls)

    def register_control(self, control):
        registered_controls = self.get_current_kontroller()
        control_meta = getattr(self, control)._control_meta
        row_to_register = pd.DataFrame([control_meta])

        combinations = list(itertools.product(*self.applies_to_subset.values()))

        df_expanded = pd.DataFrame(combinations, columns=self.applies_to_subset.keys())

        rows_to_register = row_to_register.merge(df_expanded, how="cross")
        rows_to_register = rows_to_register.merge(
            registered_controls,
            how="outer",
            on=[*self.applies_to_subset.keys(), *control_meta.keys()],
            indicator=True,
        )
        rows_to_register = rows_to_register[
            rows_to_register["_merge"] == "left_only"
        ].drop(columns=["_merge"])
        if rows_to_register.empty:
            logger.debug("No new control to register, ending here.")
            return None
        if isinstance(self.conn, EimerDBInstance):
            self.conn.insert("kontroller", rows_to_register)
        elif conn_is_ibis(self.conn):
            conn = self.conn
            k = conn.table("kontroller")
            k.insert(rows_to_register)
        else:
            raise NotImplementedError(
                f"Connection type '{type(self.conn)}' is currently not implemented."
            )

    def register_all_controls(self):
        self.find_control_methods()
        for control in self.controls:
            self.register_control(control)

    def get_current_kontroller(self):
        if isinstance(self.conn, EimerDBInstance):
            conn = ibis.polars.connect()
            kontroller = self.conn.query(
                "SELECT * FROM kontroller"
            )  # maybe add something like this?partition_select=self.applies_to_subset
            conn.create_table("kontroller", kontroller)
        elif conn_is_ibis(self.conn):
            conn = self.conn
        else:
            raise NotImplementedError(
                f"Connection type '{type(self.conn)}' is currently not implemented."
            )
        kontroller = conn.table("kontroller")
        kontroller = kontroller.filter(
            ibis_filter_with_dict(self.applies_to_subset)
        ).to_pandas()
        logger.debug(f"Kontroller\n{kontroller}")
        print(f"Kontroller\n{kontroller}")
        return kontroller

    def execute_controls(self) -> None:
        control_results = self.run_all_controls()
        self.update_existing_records(control_results)
        self.insert_new_records(control_results)

    def run_all_controls(self):
        self.find_control_methods()

        df_all_results: list[pd.DataFrame] = []
        for method_name in self.controls:
            logger.debug(f"Running method: {method_name}")
            print(f"Running method: {method_name}")
            if not callable(getattr(self, method_name)):
                raise TypeError(
                    f"Attribute in class '{method_name}' is not callable. Either make it a method or change its name to not start with 'control_'."
                )
            df_all_results.append(self.run_control(method_name))
        df = pd.concat(df_all_results).reset_index(drop=True)

        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"Control results is not a pandas dataframe, is type: {type(df)}"
            )
        return df

    def run_control(self, control: str) -> pd.DataFrame:
        """Runs a single control.

        Args:
            control: Name of a control method to run implemented in the supplied control class built upon ControlFrameworkBase.

        Returns:
            pd.Dataframe: Dataframe containing results from the control.

        Raises:
            TypeError: If control method does not return pd.dataframe.
        """
        results = getattr(self, control)()
        if not isinstance(results, pd.DataFrame):
            raise TypeError(
                f"Result from control method is not a pd.dataframe. Received: '{type(results)}'"
            )
        for column in self._required_kontrollutslag_columns:
            if column not in results.columns:
                raise ValueError(
                    f"Missing required column '{column}' for result from '{control}'."
                )
        return results

    def get_current_kontrollutslag(self):
        if isinstance(self.conn, EimerDBInstance):
            conn = ibis.polars.connect()
            kontrollutslag = self.conn.query(
                "SELECT * FROM kontrollutslag"
            )  # maybe add something like this?partition_select=self.applies_to_subset
            conn.create_table("kontrollutslag", kontrollutslag)
        elif conn_is_ibis(self.conn):
            conn = self.conn
        else:
            raise NotImplementedError(
                f"Connection type '{type(self.conn)}' is currently not implemented."
            )
        kontrollutslag = conn.table("kontrollutslag")
        kontrollutslag = kontrollutslag.filter(
            ibis_filter_with_dict(self.applies_to_subset)
        ).to_pandas()
        logger.debug(f"Kontrollutslag\n{kontrollutslag}")
        return kontrollutslag

    def insert_new_records(self, control_results):
        existing_kontrollutslag = self.get_current_kontrollutslag()
        if existing_kontrollutslag.empty:
            logger.debug("No existing rows found.")
        merged = control_results.merge(
            existing_kontrollutslag,
            on=[*self.applies_to_subset.keys(), "kontrollid", "ident", "refnr"],
            how="outer",
            indicator=True,
        )
        merged = (
            merged[merged["_merge"] == "left_only"][
                [
                    *self.applies_to_subset.keys(),
                    "kontrollid",
                    "ident",
                    "refnr",
                    "verdi_x",
                    "utslag_x",
                ]
            ]
            .rename(columns={"utslag_x": "utslag", "verdi_x": "verdi"})
            .dropna()
        )
        if merged.empty:
            logger.debug("No new rows found, ending here.")
            return None
        # Now to insert new rows into the table.
        if isinstance(self.conn, EimerDBInstance):
            self.conn.insert("kontrollutslag", merged)
        elif conn_is_ibis(self.conn):
            conn = self.conn
            k = conn.table("kontrollutslag")
            k.insert(merged)
        else:
            raise NotImplementedError(
                f"Connection type '{type(self.conn)}' is currently not implemented."
            )
        logger.debug(f"Inserted {merged.shape[0]} new rows to kontrollutslag.")

    def update_existing_records(self, control_results):
        existing_kontrollutslag = self.get_current_kontrollutslag()
        if existing_kontrollutslag.empty:
            logger.debug("No existing rows found, ending here.")
            return None
        merged = control_results.merge(
            existing_kontrollutslag,
            on=["kontrollid", "ident", "refnr"],
            how="outer",
            indicator=True,
        ).dropna()
        changed = merged[merged["utslag_x"] != merged["utslag_y"]][
            ["kontrollid", "ident", "refnr", "verdi_x", "utslag_x"]
        ].rename(columns={"utslag_x": "utslag", "verdi_x": "verdi"})
        if changed.empty:
            logger.debug("No changed rows, ending here.")
            return None
        update_query = self.generate_update_query(changed)
        if isinstance(self.conn, EimerDBInstance):
            self.conn.query(update_query)
        elif conn_is_ibis(self.conn):
            conn = self.conn
            conn.raw_sql(update_query)
        else:
            raise NotImplementedError(
                f"Connection type '{type(self.conn)}' is currently not implemented."
            )
        print(f"UPDATING {changed.shape[0]}")

    def generate_update_query(self, df_updates: pd.DataFrame) -> str:
        """Generates a SQL UPDATE query for updating rows in 'kontrollutslag'.

        Args:
            df_updates (pd.DataFrame): DataFrame with updates to apply.

        Returns:
            str: SQL query string.
        """
        update_query = "UPDATE kontrollutslag SET utslag = CASE"

        for _, row in df_updates.iterrows():
            update_query += (
                f" WHEN kontrollid = '{row['kontrollid']}' AND "
                f"refnr = '{row['refnr']}' THEN {row['utslag']}"
            )

        update_query += " ELSE utslag END"
        update_query += (
            " WHERE "
            + " OR ".join(
                [
                    f"(kontrollid = '{row['kontrollid']}' AND refnr = '{row['refnr']}')"
                    for _, row in df_updates.iterrows()
                ]
            )
            + ";"
        )
        logger.debug(f"Update query:\n{update_query}")

        return update_query

    @control(
        kontrollid="diff",
        kontrolltype="endring",
        skildring="Stor differanse mot fjoråret",
        kontrollvariabel="fulldyrket",
        sorteringsvariabel=None,
    )
    def control_diff(self):
        aar = int(self.applies_to_subset["aar"][0])
        df = self.conn.query("SELECT * FROM skjemadata_hoved")
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

    @control(
        kontrollid="bunnfradrag",
        kontrolltype="mulig_feil",
        skildring="Ikke 6000",
        kontrollvariabel="bunnfradrag",
        sorteringsvariabel=None,
    )
    def control_bunnfradrag(self):
        aar = int(self.applies_to_subset["aar"][0])
        df = self.conn.query(
            f"SELECT * FROM skjemadata_hoved WHERE variabel = 'bunnfradrag' AND aar = {aar}"
        )

        df["utslag"] = False
        df["verdi"] = df["verdi"].astype(float).astype(int)
        df.loc[((df["verdi"]) != 6000), "utslag"] = True

        df["aar"] = aar
        df["skjema"] = "RA-7357"
        df["kontrollid"] = "bunnfradrag"

        return df[["aar", "skjema", "ident", "refnr", "kontrollid", "utslag", "verdi"]]


if __name__ == "__main__":
    import eimerdb as db

    conn = db.EimerDBInstance(
        "ssb-dapla-felles-data-produkt-prod",
        "produksjonstilskudd_altinn3",
    )

    res = conn.query("SELECT * FROM kontroller")

    res = conn.query("SELECT * FROM kontrollutslag")

    test = ControlFrameworkBase(
        time_units=["aar"],
        applies_to_subset={"aar": [2020], "skjema": ["RA-7357"]},
        conn=conn,
    )

    test.register_all_controls()

    test.execute_controls()
