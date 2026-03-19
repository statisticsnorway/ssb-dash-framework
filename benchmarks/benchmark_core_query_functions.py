import argparse
import csv
import json
import statistics
import timeit
from datetime import datetime
from urllib.parse import quote_plus
import os
from ibis import _
from ssb_dash_framework.utils.config_tools.connection import (
    _get_connection_object,
    get_connection,
    set_eimerdb_connection,
    set_postgres_connection,
)
from ssb_dash_framework.utils.core_query_functions import (
    active_no_duplicates_refnr_list,
)

user = (
    "strukt-naering-developers@dapla-group-sa-p-ye.iam"
    if os.getenv("DAPLA_ENVIRONMENT") == "PROD"
    else "strukt-naering-developers@dapla-group-sa-t-57.iam"
)
encoded_user = quote_plus(user)
conn_url = "host=localhost port=5432 dbname=strukt-naering user=strukt-naering-developers@dapla-group-sa-p-ye.iam options=-csearch_path=naringer"
set_postgres_connection(database_url=conn_url)

# from ssb_dash_framework import set_eimerdb_connection

# set_eimerdb_connection(
#     bucket_name="ssb-dapla-felles-data-produkt-prod",
#     eimer_name="produksjonstilskudd_altinn3",
# )

# for table in _get_connection_object().tables:
#     _get_connection_object().combine_inserts(table, raw=False)
#     _get_connection_object().combine_changes(table)

def get_connection_type() -> str:
    """Return a short lowercase label for the active connection type, e.g. 'postgres' or 'eimerdb'."""
    try:
        obj = _get_connection_object()
        return type(obj).__name__.lower()
    except Exception:
        return "unknown"

#################
#  Preparation  #
#################

with get_connection(necessary_tables = ["skjemamottak"], partition_select={"aar": [2018]}) as conn:
    test_refnr = active_no_duplicates_refnr_list(conn)[0]
    t = conn.table("skjemamottak")
    test_ident = t.filter(_.refnr == test_refnr)


##########################
#  Queries to benchmark  #
##########################

# Test getting refnrs and all active data

def benchmark_active_no_duplicates_refnr_list():
    with get_connection(necessary_tables = ["skjemamottak"], partition_select={"aar": [2018]}) as conn:
        return active_no_duplicates_refnr_list(conn)


def benchmark_get_active_data_execute():
    with get_connection(necessary_tables = ["skjemamottak", "skjemadata_hoved"], partition_select={"aar": [2018]}) as conn:
        t = conn.table("core_skjemadata")
        relevant_refnr = active_no_duplicates_refnr_list(conn)
        return t.filter(t.refnr.isin(relevant_refnr)).execute()


def benchmark_get_active_data_pandas():
    with get_connection(necessary_tables = ["skjemamottak", "skjemadata_hoved"], partition_select={"aar": [2018]}) as conn:
        t = conn.table("core_skjemadata")
        relevant_refnr = active_no_duplicates_refnr_list(conn)
        return t.filter(t.refnr.isin(relevant_refnr)).to_pandas()


###########################
#  Code for benchmarking  #
###########################
 
def benchmark_func(func, repeat: int = 10, number: int = 5) -> dict:
    """
    Time *func* and return summary statistics.
 
    Parameters
    ----------
    func:    zero-argument callable to benchmark
    repeat:  number of timing runs (outer loop)
    number:  calls per run (inner loop) — per-call avg is reported
    """
    # Warmup: one un-timed call to avoid cold starts disrupting results.
    try:
        func()
    except Exception as e:
        return {"error": str(e)}
 
    try:
        timer = timeit.Timer(func)
        raw = timer.repeat(repeat=repeat, number=number)
    except Exception as e:
        return {"error": str(e)}
 
    per_call = [t / number for t in raw]
    return {
        "min":    min(per_call),
        "max":    max(per_call),
        "mean":   statistics.mean(per_call),
        "median": statistics.median(per_call),
        "stdev":  statistics.stdev(per_call) if len(per_call) > 1 else 0.0,
        "repeat": repeat,
        "number": number,
    }
 
 
def run_benchmarks(funcs: list, repeat: int = 10, number: int = 5) -> dict:
    results = {}
    total_start = timeit.default_timer()
 
    for func in funcs:
        print(f"Benchmarking {func.__name__}...")
        results[func.__name__] = benchmark_func(func, repeat=repeat, number=number)
 
    results["_meta"] = {
        "wall_seconds": round(timeit.default_timer() - total_start, 3),
        "timestamp":    datetime.now().isoformat(timespec="seconds"),
        "repeat":       repeat,
        "number":       number,
    }
    return results
 
 
########################
#  Output / reporting  #
########################
 
_COL_W = 14
 
 
def _fmt(value, decimals: int = 4) -> str:
    if isinstance(value, float):
        return f"{value:.{decimals}f}s"
    return str(value)
 
 
def print_results(results: dict) -> None:
    meta = results.get("_meta", {})
    func_results = {k: v for k, v in results.items() if not k.startswith("_")}
 
    print(
        f"\nResults  (repeat={meta.get('repeat')}, number={meta.get('number')}, "
        f"wall={meta.get('wall_seconds')}s, {meta.get('timestamp')})"
    )
    cols = ["min", "max", "mean", "median", "stdev"]
    header = f"{'function':<45}" + "".join(f"{c:>{_COL_W}}" for c in cols)
    print(header)
    print("-" * len(header))
 
    for name, stats in func_results.items():
        if "error" in stats:
            print(f"{name:<45}  ERROR: {stats['error']}")
        else:
            row = f"{name:<45}" + "".join(f"{_fmt(stats[c]):>{_COL_W}}" for c in cols)
            print(row)
    print()
 
 
def save_results(results: dict, path: str) -> None:
    if path.endswith(".json"):
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
    elif path.endswith(".csv"):
        meta = results.get("_meta", {})
        rows = [
            {
                "function": name,
                "timestamp": meta.get("timestamp"),
                "repeat": meta.get("repeat"),
                "number": meta.get("number"),
                **stats,
            }
            for name, stats in results.items()
            if not name.startswith("_")
        ]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    print(f"Results saved to {path}")
 
 
#################
#  Entry point  #
#################
 
ALL_BENCHMARKS = [
    benchmark_active_no_duplicates_refnr_list,
    benchmark_get_active_data_execute,
    benchmark_get_active_data_pandas,
]
from pathlib import Path
RESULTS_DIR = Path("/home/onyxia/work/ssb-dash-framework/benchmarks/results")


if __name__ == "__main__":
    _conn_type = get_connection_type()
    _default_output = RESULTS_DIR / f"benchmark_{_conn_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
 
    parser = argparse.ArgumentParser(description="Run query benchmarks")
    parser.add_argument(
        "--repeat", type=int, default=10,
        help="Number of timing runs per function (default: 10)",
    )
    parser.add_argument(
        "--number", type=int, default=5,
        help="Calls per timing run (default: 5)",
    )
    parser.add_argument(
        "--filter", type=str, default=None,
        help="Only run benchmarks whose name contains this substring",
    )
    parser.add_argument(
        "--output", type=str, default=str(_default_output),
        help=f"Save results to this file (.json or .csv) (default: {_default_output})",
    )
    args = parser.parse_args()
 
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
 
    funcs = ALL_BENCHMARKS
    if args.filter:
        funcs = [f for f in funcs if args.filter in f.__name__]
        if not funcs:
            print(f"No benchmarks matched filter '{args.filter}'")
            raise SystemExit(1)
 
    results = run_benchmarks(funcs, repeat=args.repeat, number=args.number)
    print_results(results)
    save_results(results, args.output)