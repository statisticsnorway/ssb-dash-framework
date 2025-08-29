import logging

import pandas as pd

logger = logging.getLogger(__name__)


class ControlFrameworkBase:  # TODO: Add some common control methods here for easier reuse.
    """Base class for running control checks.

    Designed to work on partitioned data following the recommended altinn3 data structure. Manages inserts and updates
    to the 'kontrollutslag' table via a connection interface.

    The flow of updating the control table works like this:

        1. First call 'execute_controls', this begins the entire process.
        2. 'control_updates' is run, during which the code checks existing controls, runs all controls and creates a dataframe with all results.
            'run_all_controls' is run, which in turn calls 'run_control' for each individual control.
            The results from control_updates is used to check if there has been any changes since last executing controls. If there are no changes, the process stops here.
        3. Based on the results from 'control_updates' it generates an update query where each change in the results, where the result of a control has changed for an observation, is updated in the 'kontrollutslag' table.
        4. The update query is run, and the process is complete.
    """

    def __init__(
        self,
        partitions: list[int | str],
        partitions_skjema: dict[str, int | str],
        conn: object,
    ) -> None:
        """Initialize the control framework.

        Args:
            partitions: Partition to execute controls on.
            partitions_skjema: Partition specification, including skjema.
            conn: Database connection object with query and insert methods.
        """
        if not hasattr(conn, "query"):
            raise AttributeError("The 'conn' object must have a 'query' method.")
        if not hasattr(conn, "insert"):
            AttributeError("The 'conn' object must have a 'insert' method.")
        self.partitions = partitions
        self.partitions_skjema = partitions_skjema
        self.conn = conn
        self.controls = self.conn.query(
            "SELECT kontrollid FROM kontroller",
            partition_select=partitions_skjema,
        )["kontrollid"].tolist()
        logger.debug(self.controls)

    def execute_controls(self) -> int:
        """Executes control checks and updates existing rows in 'kontrollutslag' if needed.

        Returns:
            int: Number of rows updated.
        """
        df_updates = self.control_updates()
        if len(df_updates) > 0:
            print(f"{len(df_updates)} rader oppdateres...")
            self.conn.query(
                self.generate_update_query(df_updates), self.partitions_skjema
            )
            print("Oppdatering fullført!")
        else:
            print("Ingen rader å oppdatere")
        return len(df_updates)

    def control_updates(self) -> pd.DataFrame:
        """Identifies rows in 'kontrollutslag' where the control output has changed.

        Returns:
            pd.DataFrame: DataFrame of rows that need to be updated.
        """
        df_allerede_kontrollert = self.conn.query(
            "SELECT kontrollid, ident, refnr, utslag FROM kontrollutslag",
            self.partitions_skjema,
        )
        df = self.run_all_controls()
        total_merge = df.merge(
            df_allerede_kontrollert,
            on=["kontrollid", "ident", "refnr"],
            how="outer",
            indicator=True,
        ).dropna()

        df_endrede = total_merge[total_merge["utslag_x"] != total_merge["utslag_y"]][
            ["kontrollid", "ident", "refnr", "verdi", "utslag_x"]
        ].rename(columns={"utslag_x": "utslag"})

        return df_endrede

    def run_all_controls(self) -> pd.DataFrame:
        """Runs control methods named like 'control_<kontrollid>' where <id> is in self.controls.

        Returns:
            pd.DataFrame: Combined DataFrame with all control results.

        Raises:
            TypeError: if 'df' variable to return is not pd.DataFrame.
        """
        df_all_results: list[pd.DataFrame] = []
        for method_name in dir(self):
            if method_name[8:] in self.controls and method_name.startswith("control_"):
                if not callable(getattr(self, method_name)):
                    raise TypeError(
                        f"Attribute in class '{method_name}' is not callable. Either make it a method or change its name to not start with 'control_'."
                    )
                df_all_results.append(self.run_control(method_name))
            else:
                logger.debug(f"{method_name} was not called as it failed the if check.")
        df = pd.concat(df_all_results).reset_index(drop=True)
        if not isinstance(df, pd.DataFrame):
            raise TypeError(
                f"Control results is not a pandas dataframe, is type: {type(df)}"
            )
        return df

    def run_control(self, control) -> pd.DataFrame:
        results = control()
        if not isinstance(results, pd.DataFrame):
            raise TypeError(
                f"Result from control method is not a pd.dataframe. Received: '{type(results)}'"
            )
        # Check if any required columns are missing
        return results

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

        return update_query

    def control_new_rows(self) -> pd.DataFrame:
        """Identifies new rows that are not already present in 'kontrollutslag'.

        Returns:
            pd.DataFrame: DataFrame of new rows to insert.
        """
        try:
            df_allerede_kontrollert = self.conn.query(
                "SELECT aar, skjema, kontrollid, ident, refnr, utslag FROM kontrollutslag",
                self.partitions_skjema,
            )
        except Exception as e:  # TODO better exception handling.
            logger.debug(f"Exception happened:\n{e}")
            df_allerede_kontrollert = pd.DataFrame(
                columns=["aar", "skjema", "kontrollid", "ident", "refnr"]
            )
        control_results = self.run_all_controls()

        # Change below condition to 'if df_allerede_kontrollert.empty'?
        # The below part of logic should only run if there are already rows in the 'kontrollutslag' table.
        if len(df_allerede_kontrollert) != 0:  # TODO: Separate into its own method?
            total_merge = control_results.merge(
                df_allerede_kontrollert,
                on=["aar", "skjema", "kontrollid", "ident", "refnr"],
                how="outer",
                indicator=True,
            )

            control_results = total_merge[total_merge["_merge"] == "left_only"][
                [
                    "aar",
                    "skjema",
                    "kontrollid",
                    "ident",
                    "refnr",
                    "verdi",
                    "utslag_x",
                ]
            ].rename(columns={"utslag_x": "utslag"})

        return control_results

    def insert_new_rows(self) -> int:
        """Inserts any new control results that are not already in 'kontrollutslag'.

        Returns:
            int: Number of rows inserted.
        """
        df_lastes = self.control_new_rows()
        logger.debug(f"Data to insert:\n{df_lastes}")
        if len(df_lastes) > 0:
            logger.info(f"{len(df_lastes)} nye rader lastes inn...")
            self.conn.insert("kontrollutslag", df_lastes)
            logger.info("Innlasting fullført!")
        else:
            logger.info("Ingen nye rader å inserte")
        return len(df_lastes)
