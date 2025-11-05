"""TERMPORARILY DISABLED UNTIL A SERVICE IN DAPLA LAB WITH R AND PYTHON FOR VSCODE EXISTS.

This module contains utility functions for R-related tasks in the SSB Dash Framework.
"""

import logging
import timeit

import pandas as pd
from rpy2.robjects import conversion
from rpy2.robjects import default_converter
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import InstalledSTPackage
from rpy2.robjects.packages import PackageNotInstalledError
from rpy2.robjects.packages import importr

logger = logging.getLogger(__name__)

# Global variable to store the R package Kostra
_kostra_r: InstalledSTPackage | None = None

_attempts_kostra_r = 0

def _get_kostra_r() -> InstalledSTPackage:
    """Loads the R package Kostra.

    :return: Kostra R package
    """
    globals()["_attempts_kostra_r"] +=1
    if globals()["_attempts_kostra_r"] > 10:
        raise Exception("Something is wrong.")
    if _kostra_r is not None:
        return _kostra_r
    try:
        start_time = timeit.default_timer()
        globals()["_kostra_r"] = importr("Kostra")
        logger.info(
            "Finished loading Kostra in %3g seconds",
            (timeit.default_timer() - start_time),
        )
        return globals()["_kostra_r"]
    except PackageNotInstalledError:
        logger.warning(
            "R - Kostra not installed, trying to install and re-running _get_kostra_r. This might take a little time."
        )
        import subprocess
        commands = [
            "R -e 'renv::init()'",
            "R -e 'renv::install(\"statisticsnorway/ssb-kostra\")'"
        ]

        for command in commands:
            subprocess.run(
                command,
                shell=True,
                check=True
            )

        return _get_kostra_r()

def hb_method(
    data: pd.DataFrame,
    p_c: int,
    p_u: float,
    p_a: float,
    id_field_name: str = "id",
    x_1_field_name: str = "x1",
    x_2_field_name: str = "x2",
) -> pd.DataFrame:
    """Runs the Hb method from the R package Kostra.

    :param data: The data to run the method on
    :param p_c: The value of pC
    :param p_u: The value of pU
    :param p_a: The value of pA
    :param id_field_name: The name of the id field
    :param x_1_field_name: The name of the first x field
    :param x_2_field_name: The name of the second x field
    :return: The result of the method
    """
    with conversion.localconverter(default_converter + pandas2ri.converter):
        hb_result = _get_kostra_r().Hb(
            data=data,
            id=id_field_name,
            x1=x_1_field_name,
            x2=x_2_field_name,
            pC=p_c,
            pU=p_u,
            pA=p_a,
        )
        assert isinstance(
            hb_result, pd.DataFrame
        ), "Hb method did not return a DataFrame"
        return hb_result


def th_error(
    data: pd.DataFrame, id_field_name: str, x_1_field_name: str, x_2_field_name: str
) -> pd.DataFrame:
    """Runs the ThError method from the R package Kostra.

    :param data: The data to run the method on
    :param id_field_name: The name of the id field
    :param x_1_field_name: The name of the first x field
    :param x_2_field_name: The name of the second x field
    :return: The result of the method
    """
    with conversion.localconverter(default_converter + pandas2ri.converter):
        th_error_result = _get_kostra_r().ThError(
            data=data, id=id_field_name, x1=x_1_field_name, x2=x_2_field_name
        )
        assert isinstance(
            th_error_result, pd.DataFrame
        ), "ThError method did not return a DataFrame"
        return th_error_result[th_error_result.outlier == 0]
