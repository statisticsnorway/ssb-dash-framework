import logging
from typing import Any

import ibis
from ibis import _

logger = logging.getLogger(__name__)

"""From here and down Ibis lives."""


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


def active_no_duplicates_refnr_list(
    conn: ibis.BaseBackend, skjema: str | None = None
) -> list[
    str
]:  # TODO: Ensure that the selecting works as intended. Refactor to use table object instead of conn???
    """Takes an Ibis connection and optionally a skjema-ra-number and returns the latest refnr for each unit that is still marked as active.

    If there are more than one active refnr the latest one is returned.

    Args:
        conn (BaseBackend): An ibis connection.
        skjema (str | None): If not None filters based on a string referring to a specific form RA-number.

    Returns:
        A list of unique refnr values to select in order to get most recent and currently active response from each respondent.
    """
    skjemamottak_tbl = conn.table("skjemamottak")
    if skjema and skjema != "all":
        skjemamottak_tbl = skjemamottak_tbl.filter(skjemamottak_tbl.skjema == skjema)
    latest_per_group = skjemamottak_tbl.filter(_.aktiv).order_by(_.dato_mottatt.desc())
    return list(latest_per_group.to_pandas()["refnr"].unique())
