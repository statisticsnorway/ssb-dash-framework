import timeit
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

# user = (
#     "strukt-naering-developers@dapla-group-sa-p-ye.iam"
#     if os.getenv("DAPLA_ENVIRONMENT") == "PROD"
#     else "strukt-naering-developers@dapla-group-sa-t-57.iam"
# )
# encoded_user = quote_plus(user)
# conn_url = f"postgresql://{encoded_user}@localhost:5432/strukt-naering"
# set_postgres_connection(database_url=conn_url)

from ssb_dash_framework import set_eimerdb_connection

set_eimerdb_connection(
    bucket_name="ssb-dapla-felles-data-produkt-prod",
    eimer_name="produksjonstilskudd_altinn3",
)

for table in _get_connection_object().tables:
    _get_connection_object().combine_inserts(table, raw=False)
    _get_connection_object().combine_changes(table)

########################
# Queries to benchmark #
########################

refnr = "201839118"

def benchmark_active_no_duplicates_refnr_list():
    with get_connection(necessary_tables = ["skjemamottak"], partition_select={"aar": [2018]}) as conn:
        active_no_duplicates_refnr_list(conn)

def benchmark_get_refnr_skjemamottak():
    with get_connection(necessary_tables = ["skjemamottak"], partition_select={"aar": [2018]}) as conn:
        t = conn.table("skjemamottak")
        t.filter(_.refnr == refnr)

def benchmark_get_refnr_skjemamottak_raweimer():
    _get_connection_object().query(f"SELECT * FROM skjemamottak WHERE refnr = '{refnr}'", partition_select = {"aar": [2018]})

def benchmark_get_refnr_skjemadata_hoved():
    with get_connection(necessary_tables = ["skjemadata_hoved"], partition_select={"aar": [2018]}) as conn:
        t = conn.table("skjemadata_hoved")
        t = t.filter(_.refnr == refnr)

#########################
# Code for benchmarking #
#########################

def benchmark_func(func, repeat=10, number=100) -> dict:
    def wrapper():
        func()

    t = timeit.Timer(wrapper)
    times = t.repeat(repeat=repeat, number=number)
    avg_times = [t / number for t in times]

    return {
        "min": min(avg_times),
        "max": max(avg_times),
        "mean": sum(avg_times) / len(avg_times),
    }


def run_benchmarks(funcs: list, repeat=10, number=5) -> dict:
    results = {}
    for func in funcs:
        print(f"Benchmarking {func.__name__}...")
        results[func.__name__] = benchmark_func(func, repeat=repeat, number=number)
    return results


results = run_benchmarks(
    [
        benchmark_active_no_duplicates_refnr_list,
        benchmark_get_refnr_skjemamottak,
        benchmark_get_refnr_skjemadata_hoved,
        # benchmark_get_refnr_skjemamottak_raweimer
    ]
)

print(results)
import json
with open("benchmark_results.json", "w") as f:
    json.dump(results, f, indent=4)