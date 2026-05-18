import os
from pathlib import Path
from dash import Input, Output, State, callback, dcc
from dash.exceptions import PreventUpdate
from psycopg_pool import ConnectionPool
from ssb_dash_framework.utils.config_tools.connection import get_connection
from ssb_dash_framework.utils.config_tools.set_variables import get_time_units
from ssb_dash_framework.setup import VariableSelector
from ssb_dash_framework.utils.config_tools.connection import _get_connection_object

_STORE_CONFIGS = {}

def _scan_raw_text_for_microlayouts(yaml_file: Path, stores: dict):
    """Fallback: scan raw text for microlayout keys when yaml parsing fails."""
    with open(yaml_file) as f:
        lines = f.readlines()

    current_block = {}
    in_microlayout = False

    for line in lines:
        stripped = line.strip()
        if stripped == "type: microlayout":
            in_microlayout = True
            current_block = {}
        elif in_microlayout:
            for key in ["form_data_table", "form_reference_number_column", "form_reference_input_id"]:
                if stripped.startswith(f"{key}:"):
                    current_block[key] = stripped.split(":", 1)[1].strip()
            if stripped.startswith("layout:") or (stripped.startswith("- ") and current_block):
                # end of microlayout header
                table = current_block.get("form_data_table", "skjemadata")
                filter_col = current_block.get("form_reference_number_column", "refnr")
                input_id = current_block.get("form_reference_input_id", "var-refnr")
                if table and table not in stores:
                    stores[table] = {"filter_col": filter_col, "input_id": input_id}
                in_microlayout = False

def discover_stores_from_yaml(yaml_dir: str) -> dict[str, dict]:
    """
    Scans YAML files and returns a dict of store configs keyed by table name.
    e.g. {
        "skjemadata_foretak": {"filter_col": "refnr", "input_id": "var-refnr"},
        "saldoskjema": {"filter_col": "orgnr_foretak", "input_id": "var-ident"},
    }
    """
    import yaml

    stores = {}
    yaml_path = Path(yaml_dir)

    for yaml_file in yaml_path.rglob("*.yaml"):
        try:
            with open(yaml_file) as f:
                content = yaml.safe_load(f)
            _scan_for_microlayouts(content, stores)
        except yaml.constructor.ConstructorError:
            # file uses !include or other custom tags, scan raw text instead
            _scan_raw_text_for_microlayouts(yaml_file, stores)

    return stores


def _scan_for_microlayouts(node, stores: dict):
    """
    Recursively scan a yaml structure for microlayout nodes.
    Fetches existing tables to read from and which input-id (like "orgnr_foretak", "refnr" or "ident") that are defined.
    """
    if isinstance(node, list):
        for item in node:
            _scan_for_microlayouts(item, stores)
    elif isinstance(node, dict):
        if node.get("type") == "microlayout":
            table = node.get("form_data_table", "skjemadata")
            filter_col = node.get("form_reference_number_column", "refnr")
            input_id = node.get("form_reference_input_id", "var-refnr")
            if table not in stores:
                stores[table] = {"filter_col": filter_col, "input_id": input_id}
        for value in node.values():
            _scan_for_microlayouts(value, stores)

def get_stores(yaml_dir: str) -> list[dcc.Store]:
    """
    Created data stores to use to avoid one query per variable to the database.
    """
    global _STORE_CONFIGS
    discovered = discover_stores_from_yaml(yaml_dir)
    _STORE_CONFIGS.clear()
    _STORE_CONFIGS.update(discovered)  # mutate in place instead of reassigning
    return [dcc.Store(id=f"store-{table}") for table in _STORE_CONFIGS]


def register_store_callbacks():
    if not _STORE_CONFIGS:
        return

    store_ids = [f"store-{table}" for table in _STORE_CONFIGS]
    tables = list(_STORE_CONFIGS.keys())
    configs = list(_STORE_CONFIGS.values())

    unique_inputs = list({cfg["input_id"] for cfg in configs})

    if not isinstance(_get_connection_object(), ConnectionPool):
        print(f"Connection of type '{type(_get_connection_object())}' is not implemented yet.")
        return

    variableselector = VariableSelector(selected_inputs=[], selected_states=["aar"])

    @callback(
        [Output(store_id, "data") for store_id in store_ids],
        [Input(uid, "value") for uid in unique_inputs],
        variableselector.get_state(requested="aar"),
        prevent_initial_call=True,
    )
    def fetch_all_stores(*args):
        input_values = dict(zip(unique_inputs, args[:-1]))
        aar = args[-1]

        if not any(input_values.values()):
            raise PreventUpdate

        results = []
        with get_connection() as conn:
            for table, cfg in zip(tables, configs):
                filter_val = input_values.get(cfg["input_id"])
                if not filter_val:
                    results.append({})
                    continue
                t = conn.table(table)
                data = (
                    t.filter(t[cfg["filter_col"]] == filter_val)
                    .filter(t.aar == aar)
                    .select("variabel", "verdi")
                    .to_pandas()
                )
                results.append(data.set_index("variabel")["verdi"].to_dict())

        return results


def store_getter(skjema, refnr, ident, settings, field_path, time_units, *args):
    n_stores = len(_STORE_CONFIGS)
    
    if n_stores == 0 or len(args) < n_stores:
        from ssb_dash_framework.modules.building_blocks.microlayout_components.editable_field_model import default_getter
        return default_getter(skjema, refnr, ident, settings, field_path, time_units)
    
    store_data = args[-n_stores:]
    
    # verify they're actually dicts, not State objects
    if any(not isinstance(s, (dict, type(None))) for s in store_data):
        from ssb_dash_framework.modules.building_blocks.microlayout_components.editable_field_model import default_getter
        return default_getter(skjema, refnr, ident, settings, field_path, time_units)
    
    store_map = dict(zip(list(_STORE_CONFIGS.keys()), store_data))
    store = store_map.get(settings.form_data_table)

    if store and field_path in store:
        return store[field_path]
        
    print(f"FALLBACK to DB for {field_path} | table={settings.form_data_table} | store_empty={not store} | field_missing={store is not None and field_path not in store}")
    from ssb_dash_framework.modules.building_blocks.microlayout_components.editable_field_model import default_getter
    return default_getter(skjema, refnr, ident, settings, field_path, time_units)

    # print(f"store_getter called for {field_path} | table={settings.form_data_table} | store={'HIT' if (store and field_path in store) else 'MISS'} | _STORE_CONFIGS={list(_STORE_CONFIGS.keys())}")