import pandas as pd


class ControlFrameworkBase:
    """Base class for running control checks.

    Designed to work on partitioned data following the recommended altinn3 data structure. Manages inserts and updates
    to the 'kontrollutslag' table via a connection interface.
    """

    def __init__(
        self,
        partitions: list[int | str],
        partitions_skjema: dict[str, int | str],
        conn: object,
    ) -> None:
        """Initialize the control framework.

        Args:
            partitions: Partition specification for control execution.
            partitions_skjema: Partition specification, including skjema.
            conn: Database connection object with query and insert methods.
        """
        assert hasattr(conn, "query"), "The database object must have a 'query' method."
        assert hasattr(
            conn, "insert"
        ), "The database object must have a 'insert' method."
        self.partitions = partitions
        self.partitions_skjema = partitions_skjema
        self.conn = conn
        self.controls = self.conn.query(
            "SELECT kontrollid FROM kontroller",
            partition_select=partitions_skjema,
        )["kontrollid"].tolist()

    def _run_all_controls(self) -> pd.DataFrame:
        """Runs control methods named like 'control_<kontrollid>' where <id> is in self.controls.

        Returns:
            pd.DataFrame: Combined DataFrame with all control results.

        Raises:
            TypeError: if 'df' variable to return is not pd.DataFrame.
        """
        dfs_kontrollutslag = [
            getattr(self, method_name)()
            for method_name in dir(self)
            if (
                callable(getattr(self, method_name))
                and method_name.startswith("control_")
                and method_name.split("control_")[-1] in self.controls
            )
        ]
        df = pd.concat(dfs_kontrollutslag).reset_index(drop=True)
        if not isinstance(df, pd.DataFrame):
            raise TypeError
        return df

    def _control_new_rows(self) -> pd.DataFrame:
        """Identifies new rows that are not already present in 'kontrollutslag'.

        Returns:
            pd.DataFrame: DataFrame of new rows to insert.
        """
        try:
            df_allerede_kontrollert = self.conn.query(
                "SELECT aar, skjema, kontrollid, ident, refnr, utslag FROM kontrollutslag",
                self.partitions_skjema,
            )
        except Exception:
            df_allerede_kontrollert = pd.DataFrame(
                columns=["aar", "skjema", "kontrollid", "ident", "refnr"]
            )

        if len(df_allerede_kontrollert) == 0:
            df_lastes = self._run_all_controls()
        else:
            df = self._run_all_controls()
            total_merge = df.merge(
                df_allerede_kontrollert,
                on=["aar", "skjema", "kontrollid", "ident", "refnr"],
                how="outer",
                indicator=True,
            )

            df_lastes = total_merge[total_merge["_merge"] == "left_only"][
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

        return df_lastes

    def insert_new_rows(self) -> int:
        """Inserts any new control results that are not already in 'kontrollutslag'.

        Returns:
            int: Number of rows inserted.
        """
        df_lastes = self._control_new_rows()
        print(df_lastes)
        if len(df_lastes) > 0:
            print(f"{len(df_lastes)} nye rader lastes inn...")
            self.conn.insert("kontrollutslag", df_lastes)
            print("Innlasting fullført!")
        else:
            print("Ingen nye rader å inserte")
        return len(df_lastes)

    def _control_updates(self) -> pd.DataFrame:
        """Identifies rows in 'kontrollutslag' where the control output has changed.

        Returns:
            pd.DataFrame: DataFrame of rows that need to be updated.
        """
        df_allerede_kontrollert = self.conn.query(
            "SELECT kontrollid, ident, refnr, utslag FROM kontrollutslag",
            self.partitions_skjema,
        )
        df = self._run_all_controls()
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

    def _generate_update_query(self, df_updates: pd.DataFrame) -> str:
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

    def execute_controls(self) -> int:
        """Executes control checks and updates existing rows in 'kontrollutslag' if needed.

        Returns:
            int: Number of rows updated.
        """
        df_updates = self._control_updates()
        if len(df_updates) > 0:
            print(f"{len(df_updates)} rader oppdateres...")
            self.conn.query(
                self._generate_update_query(df_updates), self.partitions_skjema
            )
            print("Oppdatering fullført!")
        else:
            print("Ingen rader å oppdatere")
        return len(df_updates)
