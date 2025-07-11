SQL_COLUMN_CONCAT = " || '_' || "


def create_partition_select(
    desired_partitions: list[str], skjema: str | None = None, **kwargs
) -> dict[str, list[int]]:
    partition_select = {
        unit: [kwargs[unit]] for unit in desired_partitions if unit in kwargs
    }
    if skjema is not None:
        partition_select["skjema"] = [skjema]
    return partition_select
