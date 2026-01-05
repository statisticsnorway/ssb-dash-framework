import itertools
import logging
from collections.abc import Callable
from typing import Any
from typing import ClassVar

import ibis
import pandas as pd
from eimerdb import EimerDBInstance
from ibis import _

from ..utils.core_query_functions import conn_is_ibis
from ..utils.core_query_functions import ibis_filter_with_dict

logger = logging.getLogger(__name__)


def register_control(
    kontrollid: str,
    kontrolltype: str,
    beskrivelse: str,
    kontrollerte_variabler: list[str],
    sorteringsvariabel: str | None = None,
    sortering: str | None = None,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Decorator used to attach required metadata to control methods.

    It is recommended to have the name of your control method / function start with the prefix 'control_'.

    Args:
        kontrollid: The id of the control, preferably a code or shortened name. Must be unique. Note that in the control module controls are sorted alphabetically based on kontrollid, meaning you can add numbers as prefix to control the sorting order in the app.
        kontrolltype: The type of control. Must be 'H' (Hard control), 'S' (Soft control) or 'I' (Informative)
        beskrivelse: A description of the control.
        kontrollerte_variabler: A list of variables that are covered / relevant to the control.
        sorteringsvariabel: Variable to sort the values on.
        sortering: Controls if the sorting is ascending (ASC) or descending (DESC). Defaults to DESC
        **kwargs: These will be added to the `_control_meta` dict attached to the method as additional key and value pairs.

    Raises:
        TypeError: If `kontrollerte_variabler` is not a list of strings.
        ValueError: If `kontrolltype` is not one of 'H', 'S', or 'I'. Or
            if `sortering` is not one of 'ASC' or 'DESC'. Or
            if required keys are missing from the metadata dictionary.

    Returns:
        The decorated function with added attribute '_control_meta' containing a dictionary with metadata.

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

    def wrapper(func: Callable[..., Any]) -> Any:
        func._control_meta = meta_dict  # type: ignore[attr-defined]
        return func

    return wrapper


class ControlFrameworkBase:  # TODO: Add some common control methods here for easier reuse.
    """Base class for running control checks.

    Used for setting up controls with minimal boilerplate code required by the user. See Example for how to inherit from it.

    Example:
        class MyOwnControls(ControlFrameworkBase):
            def __init__(
                self,
                time_units,
                applies_to_subset,
                conn,
            ) -> None:
                super().__init__(time_units, applies_to_subset, conn)
    """

    _required_kontroller_columns: ClassVar[list[str]] = [
        "kontrollid",
        "kontrolltype",
        "beskrivelse",
    ]

    _required_kontrollutslag_columns: ClassVar[list[str]] = [
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
    ) -> None:
        """Initialize the control framework.

        Args:
            time_units: Time units that exists in the dataset.
            applies_to_subset: Subset to execute controls on.
            conn: Database connection object.
        """
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

    def find_control_methods(self) -> None:
        """Method for finding all control methods defined in the class.

        Be aware that it loops through all attributes in the class and adds any that has the '_control_meta' attribute to the list of controls.
        """
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

    def register_control(self, control: str) -> None:
        """This method registers a given control in the 'kontroller' table.

        Args:
            control: The name of the control method to register.

        Returns:
            None

        Raises:
            NotImplementedError: If connection is not EimerDBInstance or Ibis connection.
        """
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
        if registered_controls is not None:
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
            k = conn.table("kontroller")  # type: ignore[attr-defined]
            k.insert(rows_to_register)
        else:
            raise NotImplementedError(
                f"Connection type '{type(self.conn)}' is currently not implemented."
            )
        logger.info(f"Done inserting {control}")

    def register_all_controls(self) -> None:
        """Registers all controls found to the 'kontroller' table."""
        logger.info("Registering all controls.")
        self.find_control_methods()
        for control in self.controls:
            self.register_control(control)
        logger.info("All controls registered.")

    def get_current_kontroller(self) -> pd.DataFrame | None:
        """Gets the current contents of the 'kontroller' table."""
        logger.info("Getting current contents of table 'kontroller'")
        if isinstance(self.conn, EimerDBInstance):
            conn = ibis.polars.connect()
            try:
                kontroller = self.conn.query(
                    "SELECT * FROM kontroller"
                )  # maybe add something like this?partition_select=self.applies_to_subset
                conn.create_table("kontroller", kontroller)
            except (
                ValueError
            ) as e:  # TODO permanently fix this. Error caused by running .query on eimerdb table with no contents.
                if str(e) == "max() arg is an empty sequence":
                    logger.warning(
                        "Did not find any contents in 'kontroller', starting from scratch."
                    )
                    return None
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
        """Executes all control methods found in the class."""
        logger.info("Executing all controls")
        self.run_all_controls()
        logger.info("Finished executing controls.")

    def run_all_controls(self) -> pd.DataFrame:
        """Runs all controls found in the class."""
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
            TypeError: If the control method does not return a `pd.DataFrame`.
            ValueError: If a required column from `_required_kontrollutslag_columns` is missing. Or
                if the result contains extra columns that are not allowed. Or
                if the control is not registered in `self.controls`. Or
                if any key in `applies_to_subset` has too many unique values. Or
                if any value in `applies_to_subset` does not match the expected period. Or
                if the results contain more than one unique `kontrollid`. Or
                if the `kontrollid` in the results does not match the registered `_control_meta`. Or
                if there are duplicated rows in the results based on `time_units`, `ident`, and `refnr`.
        """
        logger.info(f"Running control: {control}")
        results = getattr(self, control)()

        logger.debug("Starting validation of results.")
        if not isinstance(results, pd.DataFrame):
            raise TypeError(
                f"Result from control method is not a pd.dataframe. Received: '{type(results)}'"
            )
        if "kontrollid" not in results.columns:
            results["kontrollid"] = getattr(self, control)._control_meta["kontrollid"]
        for column in self._required_kontrollutslag_columns:
            if column not in results.columns:
                raise ValueError(
                    f"Missing required column '{column}' for result from '{control}'."
                )
        allowed = set([*self._required_kontrollutslag_columns, "skjema", "verdi"])
        current = set(results.columns)
        extra_columns = current - allowed
        if extra_columns:
            raise ValueError(
                f"In order to prevent errors, unnecessary columns needs to be removed from result of {control}: {extra_columns}\n\nOne possible solution is ending your control code with this 'return df[['aar', 'kvartal', 'skjema', 'ident', 'refnr', 'kontrollid', 'utslag', 'verdi']]'"
            )
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
            raise ValueError(
                f"The results contains to many unique values for the column 'kontrollid': {unique_controlids}"
            )
        if unique_controlids[0] != getattr(self, control)._control_meta["kontrollid"]:
            raise ValueError(
                f"The registered kontrollid for this control is '{getattr(self, control)._control_meta['kontrollid']}', but your results contain '{unique_controlids[0]}'. These must be identical."
            )
        if results.duplicated(subset=[*self.time_units, "ident", "refnr"]).any():
            logger.debug(
                f"Duplicates found in results from {control}:\n{results[results.duplicated(subset=[*self.time_units, 'ident', 'refnr'], keep=False)]}"
            )
            raise ValueError(f"There are duplicated rows in the results for {control}.")
        logger.info(
            f"Finished running {control}, proceeding with updating data. Results from control:\n{results['utslag'].value_counts()}"
        )
        self.update_existing_records(results)
        self.insert_new_records(results)
        logger.info(f"Updated kontrollutslag based on new run of '{control}'")
        return results

    def get_current_kontrollutslag(
        self, specific_control: str | None = None
    ) -> pd.DataFrame | None:
        """Method to get current content of the kontrollutslag table.

        Args:
            specific_control: Gets the current content of kontrollutslag table for this control. Defaults to None, which returns the data for all controls.

        Returns:
            pd.DataFrame containing the current kontrollutslag table for all controls or just the specified one or None if table empty.

        Raises:
            NotImplementedError: If connection is not EimerDBInstance or Ibis connection.
        """
        logger.info("Getting current kontrollutslag.")
        if isinstance(self.conn, EimerDBInstance):
            conn = ibis.polars.connect()
            try:
                kontrollutslag = self.conn.query(
                    "SELECT * FROM kontrollutslag"
                )  # maybe add something like this?partition_select=self.applies_to_subset
                conn.create_table("kontrollutslag", kontrollutslag)
            except (
                ValueError
            ) as e:  # TODO permanently fix this. Error caused by running .query on eimerdb table with no contents.
                if str(e) == "max() arg is an empty sequence":
                    logger.warning(
                        "Did not find any contents in 'kontrollutslag', starting from scratch."
                    )
                    return None
                else:
                    raise e

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
        logger.debug(
            f"Existing kontrollutslag\nAmount:{kontrollutslag['utslag'].value_counts()}\nData:\n{kontrollutslag}"
        )
        return kontrollutslag

    def insert_new_records(self, control_results: pd.DataFrame) -> None:
        """Inserts new records that are not found in the current contents of the 'kontrollutslag' table."""
        if control_results["kontrollid"].nunique() == 1:
            specific_control = next(iter(control_results["kontrollid"].unique()))
        else:
            specific_control = None
        existing_kontrollutslag = self.get_current_kontrollutslag(specific_control)
        if existing_kontrollutslag is not None:
            control_results = control_results.merge(
                existing_kontrollutslag,
                on=[*self.applies_to_subset.keys(), "kontrollid", "ident", "refnr"],
                how="outer",
                indicator=True,
            )
            control_results = (
                control_results[control_results["_merge"] == "left_only"][
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
        else:
            logger.debug("No existing rows found.")
        if control_results.empty:
            logger.debug("No new rows found, ending here.")
            return None
        # Now to insert new rows into the table.
        logger.debug(f"Inserting {control_results.shape[0]} new rows.")
        if isinstance(self.conn, EimerDBInstance):
            self.conn.insert("kontrollutslag", control_results)
        elif conn_is_ibis(self.conn):
            conn = self.conn
            k = conn.table("kontrollutslag")  # type: ignore[attr-defined]
            k.insert(control_results)
        else:
            raise NotImplementedError(
                f"Connection type '{type(self.conn)}' is currently not implemented."
            )
        logger.debug("Finished inserting new rows.")

    def update_existing_records(self, control_results: pd.DataFrame) -> None:
        """Updates the 'kontrollutslag' table based on results from new run of the method."""
        logger.debug("Starting process.")

        if control_results["kontrollid"].nunique() == 1:
            specific_control = next(iter(control_results["kontrollid"].unique()))
        else:
            specific_control = None
        existing_kontrollutslag = self.get_current_kontrollutslag(specific_control)
        logger.debug(
            f"control_results:\n{control_results}\nexisting_kontrollutslag:\n{existing_kontrollutslag}"
        )
        if existing_kontrollutslag is None or existing_kontrollutslag.empty:
            logger.info("No existing rows found, ending here.")
            return None
        else:
            control_results = control_results.merge(
                existing_kontrollutslag,
                on=["kontrollid", "ident", "refnr"],
                how="outer",
                indicator=True,
            ).dropna()
        if control_results.empty:
            raise ValueError(
                "Combined results from 'control_results' and 'existing_kontrollutslag' is empty."
            )
        logger.debug(control_results)
        logger.debug(
            f"Utslag left:\n{control_results['utslag_x'].value_counts()}\nUtslag right:\n{control_results['utslag_y'].value_counts()}"
        )
        changed = control_results[
            control_results["utslag_x"] != control_results["utslag_y"]
        ][["kontrollid", "ident", "refnr", "verdi_x", "utslag_x"]].rename(
            columns={"utslag_x": "utslag", "verdi_x": "verdi"}
        )
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
            conn.raw_sql(update_query)  # type: ignore[attr-defined]
        else:
            raise NotImplementedError(
                f"Connection type '{type(self.conn)}' is currently not implemented."
            )
        logger.debug("Finished updating kontrollutslag.")

    def generate_update_query(self, df_updates: pd.DataFrame) -> str:
        """Generates a SQL UPDATE query for updating rows in 'kontrollutslag'.

        Args:
            df_updates: DataFrame with updates to apply.

        Returns:
            SQL query string.
        """
        update_query = "UPDATE kontrollutslag SET utslag = CASE"

        for _index, row in df_updates.iterrows():
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
