import logging
import warnings

import pandas as pd

logger = logging.getLogger(__name__)



def control(kontroll_id, kontrolltype, skildring,kontrollvariabel,sorteringsvariabel, **kwargs):
    """
    Decorator used to attach REQUIRED metadata to control_<id> methods.

    Required fields:
        - kontroll_id
        - kontrolltype
        - skildring
        - kontrollvariabel
        - sorteringsvariabel
    """
    required_keys = {
        "kontroll_id",
        "kontrolltype",
        "skildring",
        "kontrollvariabel",# Optional?
        "sorteringsvariabel", # Optional?
    }
    meta_dict = {
        "kontroll_id": kontroll_id,
        "kontrolltype": kontrolltype,
        "skildring": skildring,
        "kontrollvariabel": kontrollvariabel,
        "sorteringsvariabel": sorteringsvariabel,
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
        time_units: list[int | str],
        applies_to_forms: list[str],
        conn: object,
        partitions: list[int | str] | None = None, # Deprecated name
        partitions_skjema: dict[str, int | str] | None= None, # Deprecated name
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
                stacklevel=2
            )
            # Map old to new
            if time_units is None:
                time_units = partitions
            if applies_to_forms is None:
                # Needs transformation here
                applies_to_forms = partitions_skjema
        self.time_units = time_units
        self.applies_to_forms = applies_to_forms

        self._required_kontroller_columns = [*self.time_units, *ControlFrameworkBase._required_kontroller_columns]
        self._required_kontrollutslag_columns = [*self.time_units, *ControlFrameworkBase._required_kontrollutslag_columns]


    def find_control_methods(self):
        self.controls = []
        for method_name in dir(self):
            if hasattr(getattr(test, method_name), "_control_meta"):
                self.controls.append(method_name)
        if len(self.controls) == 0:
            raise ValueError("No control methods found.")
        print(self.controls)

    def register_controls(self):
        self.find_control_methods()


        

    def execute_controls(self) -> None:
        control_results = self.run_all_controls()
        print(control_results)


    def run_all_controls(self):
        self.find_control_methods()

        df_all_results: list[pd.DataFrame] = []
        for method_name in self.controls:
            logger.debug(f"Running method: {method_name}")
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
                raise ValueError(f"Missing required column '{column}' for result from '{control}'.")
        return results

    
    def insert_new_records(self):
        ...
    
    def update_existing_records(self):
        ...



    @control(
        kontroll_id="standard_1",
        kontrolltype="info",
        skildring="Skjemaet har en kommentar",
        kontrollvariabel=None,
        sorteringsvariabel=None
    )
    def control_comment_exists(self):
        conn = db.EimerDBInstance(
        "ssb-dapla-felles-data-produkt-prod",
        "produksjonstilskudd_altinn3",
        )
        res = conn.query("SELECT * FROM kontaktinfo WHERE aar = '2018'")
        return res



if __name__ == "__main__":
    import eimerdb as db

    conn = db.EimerDBInstance(
        "ssb-dapla-felles-data-produkt-prod",
        "produksjonstilskudd_altinn3",
    )
    res = conn.query("SELECT * FROM kontaktinfo WHERE aar = '2018'")
    print(res)

    test = ControlFrameworkBase(
        time_units=["aar"],
        applies_to_forms=["RA-7357"],
        conn=None
    )

    test.register_controls()

    test.execute_controls()