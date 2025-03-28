import os
import glob
from pathlib import Path
import logging
import time
import pickle
from datetime import datetime
from sklearn.model_selection import train_test_split
import pandas as pd
import eimerdb as db
from statstruk import ratemodel
from functools import cache

logger = logging.getLogger(__name__)

bucket = "ssb-dapla-felles-data-produkt-prod"
db_name = "produksjonstilskudd"
conn = db.EimerDBInstance(bucket, db_name)

variables = ["arealtilskudd", "fulldyrket"]

# +
enhetsinfo = conn.query("SELECT * FROM enhetsinfo WHERE soeknads_aar = '2024'")

enhetsinfo = enhetsinfo.loc[enhetsinfo["variable"] == "saksbehandlende_kommune"].assign(fylke=lambda x: x["value"].str.zfill(4).str[:2])


# -

df = conn.query("SELECT * FROM enheter WHERE soeknads_aar = '2024'")
pop, sample = train_test_split(df, test_size=0.10)

# +
sample_orgnr = list(sample["orgnr"].unique())
pop_orgnr = list(pop["orgnr"].unique())

del df, pop, sample


# -

def get_sample(orgnr_list = sample_orgnr):
    enhetsinfo = conn.query("SELECT * FROM enhetsinfo WHERE soeknads_aar = '2024'")
    enhetsinfo = enhetsinfo.loc[enhetsinfo["variable"] == "saksbehandlende_kommune"].assign(fylke=lambda x: x["value"].str.zfill(4).str[:2])
    
    sample = conn.query(f"SELECT * FROM skjemadata WHERE orgnr IN {orgnr_list} AND soeknads_aar = '2024'")
    sample = sample.pivot_table(index="orgnr", columns = "variable", values = "value", aggfunc = "max").reset_index()
    sample = pd.merge(sample, enhetsinfo[["orgnr", "fylke"]], on="orgnr")
    for column in variables:
        sample[column] = sample[column].astype(float)
    return sample


def get_population(orgnr_list = pop_orgnr):
    enhetsinfo = conn.query("SELECT * FROM enhetsinfo WHERE soeknads_aar = '2024'")
    enhetsinfo = enhetsinfo.loc[enhetsinfo["variable"] == "saksbehandlende_kommune"].assign(fylke=lambda x: x["value"].str.zfill(4).str[:2])

    pop = conn.query(f"SELECT * FROM skjemadata WHERE orgnr IN {orgnr_list} AND soeknads_aar = '2024'")
    pop = pop.pivot_table(index="orgnr", columns = "variable", values = "value", aggfunc = "max").reset_index()
    pop = pd.merge(pop, enhetsinfo[["orgnr", "fylke"]], on="orgnr")
    for column in variables:
        pop[column] = pop[column].astype(float)
    return pop


def get_cached_model(path):
    with open(path, 'rb') as handle:
        return pickle.load(handle)
    return None


def save_cache_model(path, model):
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d-%H-%M")
    for_cache = {
        "model": model,
        "compute_time": timestamp
    }
    with open(path, 'wb') as handle:
        pickle.dump(for_cache, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return for_cache


def clear_rate_cache(path):
    files_to_remove = glob.glob(os.path.join(path, 'ratemodel_*.pickle'))
    for file_path in files_to_remove:
        try:
            os.remove(file_path)
            print(f'Removed: {file_path}')
        except Exception as e:
            print(f'Error removing {file_path}: {e}')


def ratemodell_with_caching(x_var, y_var, strata_var, id_var, get_sample_func, get_population_func, cache_location, force_rerun = False):
    start = time.time()
    logger.info("Getting model")
    cache_path = Path(f"{cache_location}/ratemodel_{x_var}_{y_var}_{strata_var}.pickle")
    if cache_path.is_file() and not force_rerun:
        logger.info("Getting model from cache")
        model_dict = get_cached_model(cache_path)
    else:
        logger.info("Calculating model")
        mod = ratemodel(get_population_func(), get_sample_func(), id_nr=id_var)
        mod.fit(x_var=x_var, y_var=y_var, strata_var=strata_var)
        model_dict = save_cache_model(cache_path, mod)
    end = time.time()
    logger.info(f"Done getting model in {end-start}")
    return model_dict


cached = ratemodell_with_caching(x_var="fulldyrket", y_var="arealtilskudd", strata_var="fylke", id_var="orgnr", get_sample_func = get_sample, get_population_func = get_population, cache_location="cache")

mod = cached["model"]

mod.get_estimates()

mod.get_imputed()

mod.get_extremes()


