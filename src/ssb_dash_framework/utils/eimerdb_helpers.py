SQL_COLUMN_CONCAT = " || '_' || "


def create_partition_select(
    desired_partitions: list[str], skjema: str | None = None, **kwargs: int
) -> dict[str, list[int | str]]:
    """Creates partition select for queries with eimerdb in callbacks.

    Args:
        desired_partitions: List of partitions you want.
        skjema: Optionally you can add which form (RA-number) you want in the partition select.
        **kwargs: Should be a dict where key is the partition and value is the specific partition you want.

    Returns:
        dict[str, list[int | str]]
    """
    partition_select: dict[str, list[int | str]] = {
        unit: [kwargs[unit]] for unit in desired_partitions if unit in kwargs
    }
    if skjema is not None:
        partition_select["skjema"] = [skjema]
    return partition_select
