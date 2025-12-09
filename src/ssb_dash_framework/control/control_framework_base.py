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
    kontrollid: str,
    kontrolltype: str,
    beskrivelse: str,
    kontrollerte_variabler: list[str],
    sorteringsvariabel: str | None = None,
    sortering: str | None = None,
    **kwargs: Any,
):
    """Decorator used to attach required metadata to control methods.

    Args:
        kontrollid (str): The id of the control, preferably a code or shortened name. Must be unique. Note that in the control module controls are sorted alphabetically based on kontrollid, meaning you can add numbers as prefix to control the sorting order in the app.
        kontrolltype (str): The type of control. Must be 'H' (Hard control), 'S' (Soft control) or 'I' (Informative)
        beskrivelse (str): A description of the control.
        kontrollerte_variabler (list[str]): A list of variables that are covered / relevant to the control.
        sorteringsvariabel (str | None): Variable to sort the values on.
        sortering (str | None): Controls if the sorting is ascending (ASC) or descending (DESC). Defaults to DESC
        kwargs (Any): These will be added to the _control_meta dict attached to the method as additional key and value pairs.

    Example:
        @register_control(
            kontrollid="001_error",
            kontrolltype="H",
            beskrivelse="Finds erroronous data.",
            kontrollerte_variabler=["revenue"],
            sorteringsvariabel="revenue",
            sortering="ASC",
        )
        def control_an_important_check(self):
            ...

    Notes:
        Some fields are required for future use with statlog-model:
        - kontrollid
        - kontrolltype
        - beskrivelse
        - kontrollerte_variabler
    """
    if not isinstance(kontrollerte_variabler, list):
        raise TypeError(
            f"'kontrollerte_variabler' must be list of strings. Received type {type(kontrollerte_variabler)}"
        )
    if kontrolltype not in ["H", "S", "I"]:
        raise ValueError(
            "'kontrolltype' must be one of 'H', 'S' or 'I'.\nH - Hard control\nS - Soft control\nI - Informative"
        )
    if sorteringsvariabel is None:
        sorteringsvariabel = ""  # TODO Maybe must be something else.
    if sortering is None:
        sortering = "DESC"
    elif sortering not in ["ASC", "DESC"]:
        raise ValueError(
            f"'sortering' must be one of 'ASC' or 'DESC'. Received '{sortering}."
        )

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
    if kwargs:
        meta_dict = meta_dict | kwargs
    for required in required_keys:
        if required not in meta_dict.keys():
            raise ValueError(f"This definition is missing required field '{required}'.")

    def wrapper(func):
        func._control_meta = meta_dict
        return func

    return wrapper


class ControlFrameworkBase:  # TODO: Add some common control methods here for easier reuse.
    """Base class for running control checks.

    Example:

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
        logger.debug("Looking for control methods.")
        self.controls = []
        for method_name in dir(self):
            if hasattr(getattr(self, method_name), "_control_meta"):
                self.controls.append(method_name)
        if len(self.controls) == 0:
            raise ValueError(
                "No control methods found. Remember to use the 'register_control' decorator function."
            )
        logger.info(f"Found controls: {self.controls}")

    def register_control(self, control):
        logger.info(f"Registering control: {control}")
        registered_controls = self.get_current_kontroller()
        control_meta = getattr(self, control)._control_meta
        row_to_register = pd.DataFrame([control_meta]).drop(
            columns=["kontrollvars"]
        )  # TODO: Fix better Dropping kontrollvars as it is included in control_meta but only clutter in the database.
        logger.debug(f"row_to_register: {row_to_register}")
        combinations = list(itertools.product(*self.applies_to_subset.values()))

        df_expanded = pd.DataFrame(combinations, columns=self.applies_to_subset.keys())
        rows_to_register = row_to_register.merge(df_expanded, how="cross")
        rows_to_register = rows_to_register.merge(
            registered_controls,
            how="outer",
            on=[
                *self.applies_to_subset.keys(),
                *[k for k in control_meta.keys() if k != "kontrollvars"],
            ],  # TODO: Fix better Dropping kontrollvars as it is included in control_meta but only clutter in the database.
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
        logger.info(f"Done inserting {control}")

    def register_all_controls(self):
        logger.info("Registering all controls.")
        self.find_control_methods()
        for control in self.controls:
            self.register_control(control)
        logger.info("All controls registered.")

    def get_current_kontroller(self):
        logger.info("Getting current contents of table 'kontroller'")
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
        logger.debug(f"Kontroller data to return:\n{kontroller}")
        return kontroller

    def execute_controls(self) -> None:
        logger.info("Executing all controls")
        self.run_all_controls()
        logger.info("Finished executing controls.")

    def run_all_controls(self):
        self.find_control_methods()

        df_all_results: list[pd.DataFrame] = []
        for method_name in self.controls:
            logger.debug(f"Running method: {method_name}")
            if not callable(getattr(self, method_name)):
                raise TypeError(
                    f"Attribute in class '{method_name}' is not callable. Either make it a method or change its name to not start with 'control_'."
                )
            result = self.run_control(method_name)
            df_all_results.append(result)
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
        
        logger.debug("Starting validation of results.")
        if not isinstance(results, pd.DataFrame):
            raise TypeError(
                f"Result from control method is not a pd.dataframe. Received: '{type(results)}'"
            )
        for column in self._required_kontrollutslag_columns:
            if column not in results.columns:
                raise ValueError(
                    f"Missing required column '{column}' for result from '{control}'."
                )
        allowed = set(self._required_kontrollutslag_columns+["skjema", "verdi"])
        current = set(results.columns)
        extra_columns = current - allowed
        if extra_columns:
            raise ValueError(f"In order to prevent errors, unnecessary columns needs to be removed from result of {control}: {extra_columns}\n\nOne possible solution is ending your control code with this 'return df[['aar', 'kvartal', 'skjema', 'ident', 'refnr', 'kontrollid', 'utslag', 'verdi']]'")
        if control not in self.controls:
            raise ValueError(
                f"Error when running {control}. Could not find {results['kontrollid'].unique()} among registered controls. Valid options retrieved from the 'kontrollutslag' table: {self.controls}"
            )
        for key, value in self.applies_to_subset.items():
            if len(results[key].unique()) != 1:
                raise ValueError(
                    f"Results from control {control} has too many unique values for '{key}'. Expected '{value[0]}'. Received: '{results[key].unique()}'"
                )
            if not value[0] == results[key].unique()[0]:
                raise ValueError(
                    f"Error when running {control}. Value for column {key} '{value[0]}' does not match period control is run for: {self.applies_to_subset}"
                )
        unique_controlids = results["kontrollid"].unique()
        if len(unique_controlids) != 1:
            raise ValueError(f"The results contains to many unique values for the column 'kontrollid': {unique_controlids}")
        if unique_controlids[0] != getattr(self, control)._control_meta["kontrollid"]:
            raise ValueError(f"The registered kontrollid for this control is '{getattr(self, control)._control_meta['kontrollid']}', but your results contain '{unique_controlids[0]}'. These must be identical.")
        if results.duplicated(subset=[*self.time_units, "ident", "refnr"]).any():
            logger.debug(f"Duplicates found in results from {control}:\n{results[results.duplicated(subset=[*self.time_units, 'ident', 'refnr'], keep=False)]}")
            raise ValueError(f"There are duplicated rows in the results for {control}.")
        logger.info(
            f"Finished running {control}, proceeding with updating data. Results from control:\n{results['utslag'].value_counts()}"
        )
        self.update_existing_records(results)
        self.insert_new_records(results)
        logger.info(f"Updated kontrollutslag based on new run of '{control}'")
        return results

    def get_current_kontrollutslag(self, specific_control = None):
        logger.info("Getting current kontrollutslag.")
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
        )
        if specific_control:
            kontrollutslag = kontrollutslag.filter(_.kontrollid == specific_control)
        kontrollutslag = kontrollutslag.to_pandas()
        logger.debug(f"Existing kontrollutslag\nAmount:{kontrollutslag['utslag'].value_counts()}\nData:\n{kontrollutslag}")
        return kontrollutslag

    def insert_new_records(self, control_results):
        if control_results["kontrollid"].nunique() == 1:
            specific_control = list(control_results["kontrollid"].unique())[0]
        else:
            specific_control = None
        existing_kontrollutslag = self.get_current_kontrollutslag(specific_control)
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
        logger.debug("Starting process.")
        if control_results["kontrollid"].nunique() == 1:
            specific_control = list(control_results["kontrollid"].unique())[0]
        else:
            specific_control = None
        existing_kontrollutslag = self.get_current_kontrollutslag(specific_control)
        if existing_kontrollutslag.empty:
            logger.info("No existing rows found, ending here.")
            return None
        logger.debug(f"control_results:\n{control_results}\nexisting_kontrollutslag:\n{existing_kontrollutslag}")
            
        merged = control_results.merge(
            existing_kontrollutslag,
            on=["kontrollid", "ident", "refnr"],
            how="outer",
            indicator=True,
        ).dropna()
        if merged.empty:
            raise ValueError(f"Combined results from 'control_results' and 'existing_kontrollutslag' is empty.")
        logger.debug(merged)
        logger.debug(f"Utslag left:\n{merged['utslag_x'].value_counts()}\nUtslag right:\n{merged['utslag_y'].value_counts()}")
        changed = merged[merged["utslag_x"] != merged["utslag_y"]][
            ["kontrollid", "ident", "refnr", "verdi_x", "utslag_x"]
        ].rename(columns={"utslag_x": "utslag", "verdi_x": "verdi"})
        if changed.empty:
            logger.info("No changed rows, ending here.")
            return None
        logger.info(f"Updating {changed.shape[0]} rows.")
        logger.debug(f"Rows to update:\n{changed}")
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
        logger.debug("Finished updating kontrollutslag.")

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
