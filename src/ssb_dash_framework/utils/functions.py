import logging
import timeit

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html
from rpy2.robjects import conversion
from rpy2.robjects import default_converter
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import InstalledSTPackage
from rpy2.robjects.packages import PackageNotInstalledError
from rpy2.robjects.packages import importr

logger = logging.getLogger(__name__)

# Global variable to store the R package Kostra
_kostra_r: InstalledSTPackage | None = None


def _get_kostra_r() -> InstalledSTPackage:
    """Loads the R package Kostra.

    :return: Kostra R package
    """
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

        command = (
            'R -e \'install.packages("remotes"); '
            'remotes::install_github("statisticsnorway/ssb-kostra")\''
        )
        subprocess.run(command, shell=True)
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


def format_timespan(start: int | float, end: int | float) -> str:
    """Formats the elapsed time between two time points into a human-readable string.

    Args:
        start (int | float): Start time in seconds, typically as a timestamp or relative value.
        end (int | float): End time in seconds, typically as a timestamp or relative value.

    Returns:
        str: A formatted string representing the elapsed time between `start` and `end`.
        The format is "MM:SS.sss (sss ms)", where:
        - MM is minutes, zero-padded to 2 digits.
        - SS.sss is seconds with 2 decimal places.
        - sss ms represents milliseconds.

    Raises:
        ValueError: If `start` is greater than `end`.
    """
    if start > end:
        raise ValueError("Start time must not be greater than end time.")

    elapsed_time = end - start
    minutes, seconds = divmod(elapsed_time, 60)
    milliseconds = (seconds - int(seconds)) * 1000
    return f"{int(minutes):0>2}:{seconds:05.2f} ({milliseconds:.0f} ms)"


def sidebar_button(
    icon: str,
    text: str,
    component_id: str,
    additional_styling: dict[str, str] | None = None,
) -> html.Div:
    """Generate a sidebar button with an icon and label.

    Args:
        icon (str): The icon displayed at the top of the button.
        text (str): The label text displayed below the icon.
        component_id (str): The ID assigned to the button component.
        additional_styling (dict, optional): Additional styling applied to the button. Defaults to an empty dictionary.

    Returns:
        html.Div: A Div containing the styled button.
    """
    if additional_styling is None:
        additional_styling = {}
    button = html.Div(
        dbc.Button(
            [
                html.Span(
                    icon,
                    style={"display": "block", "font-size": "1.4rem"}
                ),
                html.Span(
                    text,
                    style={"display": "block", "font-size": "0.7rem"}
                ),
            ],
            id=component_id,
            style={
                "display": "flex",
                "flex-direction": "column",
                "align-items": "center",
                "word-break": "break-all",
                "margin-bottom": "5%",
                "width": "100%",
                **additional_styling,
            },
        )
    )
    return button
