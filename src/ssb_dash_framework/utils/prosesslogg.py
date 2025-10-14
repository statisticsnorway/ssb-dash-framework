import pandas as pd

def apply_edits(df:pd.DataFrame, filepath_log:str, app_timestamp: datetime) -> pd.DataFrame:
    """Apply a set of logged edits to a DataFrame in a vectorized manner.

    This function updates rows in `df` based on edit records from a log
    Each edit specifies a target column (`colId`), a new value (`value`),
    and the target row identified by a UUID found inside `logg['data']`.

    Only edits with a `timestamp` later than `app_timestamp` are applied.
    If multiple edits exist for the same (uuid, colId) combination, the
    most recent one (latest row in `logg`) is kept.

    Parameters
    ----------
    df : pandas.DataFrame
        The original DataFrame containing the data to be updated.
        Must include a 'uuid' column identifying rows uniquely.

    filepath_logg : filepath for logg created by ssb-dash-framework
    
    app_timestamp : datetime
        Only edits with a timestamp greater than this value are applied.

    Returns
    -------
    pandas.DataFrame
        A copy of `df` with all applicable edits applied.

    Notes
    -----
    - Updates are applied efficiently using vectorized pandas operations.
    - Duplicate (uuid, colId) edits are resolved by keeping the last occurrence.
    - Rows in `df` without matching uuids remain unchanged.
    - This function does not modify `df` in place; it returns an edited copy.
    """
    df_edited = df.copy()
    log = pd.read_json(filepath_log,lines=True)
    log = log.loc[log['timestamp'] > app_timestamp].copy()

    log['uuid'] = log['data'].apply(lambda d: d.get('uuid') if isinstance(d, dict) else None).astype(str)

    df_edited['uuid'] = df_edited['uuid'].astype(str)

    updates = log[['uuid', 'colId', 'value']]

    updates = (
        updates.dropna(subset=['uuid', 'colId'])
        .drop_duplicates(subset=['uuid', 'colId'], keep='last')
    )

    for col, group in updates.groupby('colId'):
        mapping = group.drop_duplicates(subset=['uuid'], keep='last').set_index('uuid')['value']
        
        mapping = mapping[~mapping.index.duplicated(keep='last')]

        df_edited.loc[df_edited['uuid'].isin(mapping.index), col] = (
            df_edited['uuid'].map(mapping).fillna(df_edited[col])
        )

    return df_edited