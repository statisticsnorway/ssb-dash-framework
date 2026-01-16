import logging
from typing import Any

import ibis
import pandas as pd
from ibis import _

logger = logging.getLogger(__name__)

"""From here and down Ibis lives."""


def conn_is_ibis(conn: Any) -> bool:
    """Function to check if a supplied object is an Ibis connection.

    Used to select which 'path' to take for preparing data in modules.

    Args:
        conn: Object to check.

    Returns:
        A bool that is True if the supplied object is an Ibis connection.
    """
    if conn.__class__.__name__ == "Backend":
        logger.debug("Assuming 'self.conn' is Ibis connection.")
        return True
    else:
        return False


def create_filter_dict(
    variables: list[str], values: list[Any] | tuple[Any]
) -> dict[str, Any]:
    """Creates a filter dict for use in ibis_filter_with_dict."""
    return dict(zip(variables, values, strict=False))


def ibis_filter_with_dict(periods_dict: dict[str, Any]) -> list[Any]:
    """Creates a filter expression for Ibis.

    Args:
        periods_dict: A dictionary of column names and values to filter by.

    Returns:
        A list of filter expressions for Ibis.

    Example:
        filter_dict = {"year": "2025", "quarter": ["3", "4"]}
        t.filter(ibis_filter_with_dict(filter_dict))
    """
    filters = []
    print("Filtrerings dict")
    for key, value in periods_dict.items():
        col = getattr(_, key)
        if isinstance(value, list):
            expr = col.isin(value)
        else:
            expr = col == value
        filters.append(expr)
    print(filters)
    return filters


def active_no_duplicates_refnr_list(
    conn: ibis.BaseBackend,
    skjema: str | None = None,
    filters: dict[str, Any] | None = None,
) -> list[str]:
    """Takes an Ibis connection and optionally a skjema-ra-number and returns the latest refnr for each unit that is still marked as active.

    If there are more than one active refnr the latest one is returned.

    Args:
        conn: An ibis connection.
        skjema: If not None filters based on a string referring to a specific form RA-number.
        filters: Dict with filters to filter which subset of refnr to return.

    Returns:
        A list of unique refnr values to select in order to get most recent and currently active response from each respondent in the filtered data.

    Examples:
        result = active_no_duplicates_refnr_list(conn)
        result = active_no_duplicates_refnr_list(conn, filters={"aar": "2023"})
        result = active_no_duplicates_refnr_list(conn, skjema = "RA-9999")
        result = active_no_duplicates_refnr_list(conn, skjema = "RA-9999", filters={"aar": "2023"})
    """
    skjemamottak_tbl = conn.table("skjemamottak")
    if skjema and skjema != "all":
        skjemamottak_tbl = skjemamottak_tbl.filter(_.skjema == skjema)
    if filters:
        skjemamottak_tbl = skjemamottak_tbl.filter(ibis_filter_with_dict(filters))

    skjemamottak_tbl = skjemamottak_tbl.filter(_.aktiv).order_by(_.dato_mottatt.desc())
    return list(
        skjemamottak_tbl.to_pandas()
        .drop_duplicates(subset=["ident"], keep="first")["refnr"]
        .unique()
    )


def connect_periods_by_ident(
    conn: ibis.BaseBackend,
    current_filter: dict[str, Any],
    previous_filter: dict[str, Any],
) -> pd.DataFrame:
    """Helper function to find form from previous period by connecting through ident using the 'skjemamottak' table.

    See "Examples" for specific usage.

    Args:
        conn: Ibis connection object.
        current_filter: Filter to find the current period.
        previous_filter: Filter to find the previous period.

    Returns:
        Dataframe with columns current and previous containing current refnr and refnr from previous period from same ident.

    Examples:
        connect_periods_by_ident(
            conn,
            current_filter={"aar": "2024"},
            previous_filter={"aar": "2023"}
        )

        connect_periods_by_ident(
            conn,
            current_filter={"aar": "2024", , "kvartal": "3"},
            previous_filter={"aar": "2024", "kvartal": "2"}
        )

        connect_periods_by_ident(
            conn,
            current_filter={"aar": "2024", , "kvartal": "3"},
            previous_filter={"aar": "2023", "kvartal": "3"}
        )

    Note:
        Finds refnrs for given period using the 'active_no_duplicates_refnr_list' function.

    Raises:
        ValueError: if joined dataframe has rows where current and previous ident are not identical or previous ident is None. The latter is accepted as it shows that there is no previous form.
    """
    t = conn.table("skjemamottak")

    # Find refnrs from each period
    a = active_no_duplicates_refnr_list(conn, filters=current_filter)
    b = active_no_duplicates_refnr_list(conn, filters=previous_filter)

    # Filter each period on selected refnrs to find ident for each relevant refnr
    t0 = t.filter(_.refnr.isin(a)).select(["ident", "refnr"]).mutate(timeperiod=0)
    t1 = t.filter(_.refnr.isin(b)).select(["ident", "refnr"]).mutate(timeperiod=-1)

    # join on left so it is visible which idents have a refnr from previous period and which ones don't
    t_joined = t0.join(t1, "ident", how="left")
    t_joined = t_joined.select(["ident", "ident_right", "refnr", "refnr_right"])

    # Sanity checks
    joined_df = t_joined.to_pandas()
    if not joined_df[
        joined_df["ident"] != joined_df["ident_right"]
    ].empty and joined_df[joined_df["ident"] != joined_df["ident_right"]][
        "ident_right"
    ].unique() != [
        None
    ]:
        raise ValueError("Something wrong with join.")

    return joined_df[["refnr", "refnr_right"]].rename(
        columns={"refnr": "current", "refnr_right": "previous"}
    )
