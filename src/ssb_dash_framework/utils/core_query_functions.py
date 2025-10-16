import logging

import ibis
from ibis import _

logger = logging.getLogger(__name__)

"""From here and down Ibis lives."""

def conn_is_ibis(conn) -> bool:
    if conn.__class__.__name__ == "Backend":
        logger.debug("Assuming 'self.conn' is Ibis connection.")
        return True
    else:
        return False

def active_no_duplicates_refnr_list(conn, skjema = None): # TODO: Ensure that the selecting works as intended.
    skjemamottak_tbl = conn.table("skjemamottak")
    if skjema:
        skjemamottak_tbl = skjemamottak_tbl.filter(
            skjemamottak_tbl.skjema == skjema
        )
    latest_per_group = (
        skjemamottak_tbl
        .filter(_.aktiv)
        .order_by(_.dato_mottatt.desc())
    )
    return latest_per_group.to_pandas()["refnr"].unique()