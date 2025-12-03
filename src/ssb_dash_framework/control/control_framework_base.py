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


def register_control(
    kontrollid: str, kontrolltype: str, beskrivelse: str, kontrollerte_variabler: list[str], sorteringsvariabel: str | None = None, sortering: str | None = None, **kwargs: Any
):
    """Decorator used to attach required metadata to control_<id> methods.
    
    Some fields are for future use with statlog-model:
    - kontrollid
    - type
    - beskrivelse
    - kontrollerte_variabler
    """
    if not isinstance(kontrollerte_variabler, list):
        raise TypeError(f"'kontrollerte_variabler' must be list of strings. Received type {type(kontrollerte_variabler)}")
    if kontrolltype not in ["H", "S", "I"]:
        raise ValueError("'kontrolltype' must be one of 'H', 'S' or 'I'.\nH - Hard control\nS - Soft control\nI - Informative")
    if sorteringsvariabel is None:
        sorteringsvariabel = "" # TODO Maybe must be something else.
    if sortering is None:
        sortering = "ASC"
    elif sortering not in ["ASC", "DESC"]:
        raise ValueError(f"'sortering' must be one of 'ASC' or 'DESC'. Received '{sortering}.")

    required_keys = {
        "kontrollid",
        "type",
        "beskrivelse",
        "kontrollvars",
    }
    meta_dict = {
        "kontrollid": kontrollid,
        "type": kontrolltype,
        "beskrivelse": beskrivelse,
        "kontrollvars": kontrollerte_variabler,
        "sorting_var": sorteringsvariabel,
        "sorting_order": sortering,
    }

    for required in required_keys:
        if required not in meta_dict.keys():
            raise ValueError(f"This definition is missing required field '{required}'.")

    def wrapper(func):
        func._control_meta = meta_dict
        return func

    return wrapper


class ControlFrameworkBase:  # TODO: Add some common control methods here for easier reuse.
    """Base class for running control checks.
    """

    _required_kontroller_columns = [
        "kontrollid",
        "kontrolltype",
        "beskrivelse",
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
        for key, value in self.applies_to_subset.items():
            if not isinstance(value, list):
                self.applies_to_subset[key] = [value]
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
            if hasattr(getattr(self, method_name), "_control_meta"):
                self.controls.append(method_name)
        if len(self.controls) == 0:
            raise ValueError(
                "No control methods found. Remember to use the 'register_control' decorator function."
            )
        logger.debug(f"Found controls: {self.controls}")

    def register_control(self, control):
        logger.debug(f"Registering control: {control}")
        registered_controls = self.get_current_kontroller()
        control_meta = getattr(self, control)._control_meta
        row_to_register = pd.DataFrame([control_meta])
        # to_combine = copy.deepcopy(self.applies_to_subset)
        # for key, value in to_combine.items():
        #     if not isinstance(value, list):
        #         logger.debug(f"Value for {key} is not list. Attempting to convert {value} to list.")
        #         to_combine[key] = [value]
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
        logger.debug(f"Rows to register:\n{rows_to_register}")
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
        logger.info("Registering all controls.")
        self.find_control_methods()
        for control in self.controls:
            self.register_control(control)

    def get_current_kontroller(self):
        logger.debug("Getting current contents of table 'kontroller'")
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
        logger.info("Executing all controls")
        control_results = self.run_all_controls()
        logger.info("Updating existing results.")
        self.update_existing_records(control_results)
        logger.info("Inserting new results.")
        self.insert_new_records(control_results)
        logger.info("Finished executing controls.")

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
        logger.debug(f"Amount of control results: {df.shape[0]}")
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
        logger.info(f"Running control: {control}")
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
        logger.info(
            f"Finished running {control}. Results:\n{results['utslag'].value_counts()}"
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
        logger.debug(f"Inserting {merged.shape[0]} new rows.")
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
        logger.debug("Finished inserting new rows.")

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
        logger.info(f"Updating {changed.shape[0]} rows.")

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
        applies_to_subset={"aar": ["2020"], "skjema": ["RA-7357"]},
        conn=conn,
    )

    test.register_all_controls()

    test.execute_controls()
