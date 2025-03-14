import datetime
import json
import logging
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import Any

import dapla as dp
import pandas as pd

logger = logging.getLogger(__name__)

_error_list: list[Any] = []
_control_docs: dict[str, Any] = {}


class ControlType(Enum):
    """Enum class representing the types of quality control checks."""

    AUTOMATISK_OPPRETTING = 0
    MISSING = 1
    MULIG_FEIL = 2
    ABSOLUTT_FEIL = 3


class ErrorReport:
    """A class to detail errors found during quality control checks.

    Attributes:
        sub_control_id (str): Identifier for the sub control check.
        result_type (ControlType): The result type of the quality control check.
        context_id (str): Identifier for the context within which the error was detected.
        error_description (str, optional): A description of the error, if applicable.
        important_variables (list[str], optional): A list of important variables related to the error.
    """

    def __init__(
        self,
        sub_control_id: str,
        result_type: ControlType,
        context_id: str,
        error_description: str | None = None,
        important_variables: list[str] | None = None,
    ) -> None:
        """Initialize the error report."""
        self.sub_control_id = sub_control_id
        self.result_type = result_type
        self.context_id = context_id
        self.error_description = error_description
        self.important_variables = important_variables

    def to_dict(self) -> dict[str, Any]:
        """Converts the quality control result into a dictionary format.

        Returns:
            dict: A dictionary representing the quality control result.
        """
        return {
            "kontrollnavn": self.sub_control_id,
            "kontrolltype": self.result_type.name,
            "observasjon_id": self.context_id,
            "feilbeskrivelse": self.error_description,
            "relevante_variabler": self.important_variables,
        }


def control(
    result_type: ControlType,
    error_description: str,
    id_column: str,
    filter_for_relevant_data: Callable[[pd.DataFrame], pd.DataFrame] | None = None,
    important_variables: list[str] | None = None,
) -> Callable[[pd.DataFrame], pd.DataFrame]:
    """Decorator to define a quality control function.

    Args:
        result_type (ControlType): The type of quality control being performed.
        error_description (str): Description of the error being checked for.
        id_column (str): The column used to uniquely identify rows in the dataset.
        filter_for_relevant_data (Callable, optional): A function to filter relevant rows from the dataset.
        important_variables (list[str], optional): List of variables deemed important for the control check.

    Returns:
        Callable: A decorated function that processes the dataset and logs errors.

    Notes:
        Assumes all data given to the function is data that should be checked.
    """

    def decorator(
        control_function: Callable[[pd.DataFrame], pd.DataFrame],
    ) -> Callable[[pd.DataFrame], pd.DataFrame]:
        @wraps(control_function)
        def wrapper(data: pd.DataFrame) -> pd.DataFrame:
            data = data.copy()
            if "utslag" in data.columns:
                data = data.drop(columns=["utslag"])
                print("Droppet eksisterende utslag")
            if filter_for_relevant_data:
                total_data = data.shape[0]
                data = filter_for_relevant_data(data)
                if data.shape[0] == total_data:
                    print("Warning! Data before and after filter are the same length")
            else:
                print(
                    "Warning! Report will show 'Enheter i datasettet' and 'Enheter kontorllert' as the same amount"
                )
                total_data = None

            data["utslag"] = False
            filtered_data = control_function(data)
            error_rows = filtered_data[filtered_data["utslag"]]

            new_error_details = [
                ErrorReport(
                    sub_control_id=control_function.__name__,
                    result_type=result_type,
                    context_id=row[id_column],
                    error_description=error_description,
                    important_variables=important_variables,
                )
                for index, row in error_rows.iterrows()
            ]

            global _error_list
            _error_list.extend(new_error_details)

            global _control_docs
            _control_docs[control_function.__name__] = {
                "kontrolltype": result_type.name,
                "feilbeskrivelse": error_description,
                "docstring": control_function.__doc__,
                # Må finne en annen måte å definere antall enheter i datasett og antall enheter kontrollert
                "Enheter i datasettet": total_data if total_data else data.shape[0],
                "Enheter kontrollert": data.shape[0],
                "Kontrollutslag": error_rows.shape[0],
            }
            if important_variables:
                _control_docs[control_function.__name__][
                    "Relevante variabler"
                ] = important_variables

            data = data.drop(columns=["utslag"])

            return data

        return wrapper

    return decorator


class QualityReport:
    """A class representing the result of a quality control check.

    Attributes:
        statistics_name (str): The name of the statistics being checked.
        quality_control_id (str): The unique identifier for the quality control.
        data_location (list[str]): Locations of the data checked.
        data_period (str): The period for which the data was checked.
        quality_control_datetime (datetime.datetime): The datetime when the quality control was performed.
        quality_control_results (list[ControlType]): The results of the quality control.
        quality_control_errors (list[ErrorReport]): Detailed errors found during the quality control.
        quality_control_documentation (dict[str, str], optional): Documentation of the quality control process.
    """

    def __init__(
        self,
        statistics_name: str,
        quality_control_id: str,
        data_location: list[str],
        data_period: str,
        quality_control_datetime: datetime.datetime,
        quality_control_results: list[ControlType],
        quality_control_errors: list[ErrorReport],
        quality_control_documentation: dict[str, str] | None = None,
    ) -> None:
        """Initialize the quality control report."""
        self.statistics_name = statistics_name
        self.quality_control_id = quality_control_id
        self.data_location = data_location
        self.data_period = data_period
        self.quality_control_datetime = quality_control_datetime
        self.quality_control_results = quality_control_results
        self.quality_control_errors = quality_control_errors
        self.quality_control_documentation = quality_control_documentation

    def to_dict(self) -> dict[str, Any]:
        """Converts the quality control report into a dictionary format.

        Returns:
            dict: A dictionary representing the quality control report.
        """
        return {
            "statistikknavn": self.statistics_name,
            "quality_control_id": self.quality_control_id,  # Trengs denne?
            "data_plassering": self.data_location,
            "data_periode": self.data_period,
            "QualityReport opprettet": self.quality_control_datetime.isoformat(),
            "typer_kontrollutslag": [
                result.name for result in self.quality_control_results
            ],
            "kontrollutslag": [
                error.to_dict() for error in self.quality_control_errors
            ],
            "control_documentation": (
                self.quality_control_documentation
                if self.quality_control_documentation is not None
                else _control_docs
            ),
        }

    def save_report(self, path: str) -> None:
        """Save the quality control report to the specified path.

        Args:
            path (str): The file path where the report will be saved.
        """
        with dp.FileClient.gcs_open(path, "w") as outfile:
            json.dump(self.to_dict(), outfile)

    @classmethod
    def from_json(cls, path: str) -> "QualityReport":
        """Initialize a QualityReport from a saved JSON file.

        Args:
            path (str): Path to the JSON file.

        Returns:
            QualityReport: An instance of the quality control report.
        """
        import json

        with dp.FileClient.gcs_open(path, "r") as outfile:
            json_data = json.load(outfile)
        return cls.from_dict(json_data)

    @classmethod
    def from_dict(cls, kvalitetsrapport_dict: dict[str, Any]) -> "QualityReport":
        """Initialize a QualityReport from a dictionary.

        Args:
            kvalitetsrapport_dict (dict[str, Any]): A dictionary representing the quality control report.

        Returns:
            QualityReport: An instance of the quality control report.
        """
        statistics_name = kvalitetsrapport_dict["statistikknavn"]
        quality_control_id = kvalitetsrapport_dict["quality_control_id"]
        data_location = kvalitetsrapport_dict["data_plassering"]
        data_period = kvalitetsrapport_dict["data_periode"]
        quality_control_datetime = datetime.datetime.fromisoformat(
            kvalitetsrapport_dict["quality_report opprettet"]
        )

        quality_control_results = [
            ControlType[result]
            for result in kvalitetsrapport_dict["typer_kontrollutslag"]
        ]

        quality_control_errors = [
            ErrorReport(
                sub_control_id=error["kontrollnavn"],
                result_type=ControlType[error["kontrolltype"]],
                context_id=error["observasjon_id"],
                error_description=error.get("feilbeskrivelse"),
                important_variables=error.get("relevante_variabler"),
            )
            for error in kvalitetsrapport_dict["kontrollutslag"]
        ]
        quality_control_documentation = kvalitetsrapport_dict["control_documentation"]

        return cls(
            statistics_name=statistics_name,
            quality_control_id=quality_control_id,
            data_location=data_location,
            data_period=data_period,
            quality_control_datetime=quality_control_datetime,
            quality_control_results=quality_control_results,
            quality_control_errors=quality_control_errors,
            quality_control_documentation=quality_control_documentation,
        )


def create_quality_report(
    statistics_name: str,
    data_location: str,
    data_period: str,
    also_return_control_docs: bool = False,
) -> QualityReport | tuple[QualityReport, pd.DataFrame]:
    """Create a quality control report.

    Args:
        statistics_name (str): The name of the statistics being checked.
        data_location (str): The location of the data being checked.
        data_period (str): The period for which the data is being checked.
        also_return_control_docs (bool): Whether to return control documentation as part of the result.

    Returns:
        QualityReport | tuple[QualityReport, pd.DataFrame]:
            The quality control report or a tuple containing the report and control documentation.

    Raises:
        AssertionError: If `statistics_name`, `data_location`, or `data_period` is not provided.
    """
    assert statistics_name is not None, "Må sette statistikknavn (statistics_name)"
    assert data_location is not None, "Mangler filsti til datasett (data_location)"
    assert (
        data_period is not None
    ), "Må definere hvilken periode dataene gjelder for (data_period)"

    control_errors_nested = [_error_list]

    control_errors = [item for sublist in control_errors_nested for item in sublist]

    quality_results: list[ControlType] = []

    for i in ControlType:
        if any(error.result_type == i for error in control_errors):
            quality_results.append(i)
    if not any(quality_results):
        logger.info("No errors listed")

    report = QualityReport(
        statistics_name=statistics_name,
        quality_control_id="A reference (or link/uri) to the quality control description",
        data_location=[data_location],
        data_period=data_period,
        quality_control_datetime=datetime.datetime.now(),
        quality_control_results=quality_results,
        quality_control_errors=_error_list,
    )

    if also_return_control_docs:
        return report, create_control_documentation(report)
    else:
        return report


def create_control_documentation(
    quality_report: QualityReport | dict[str, Any],
) -> pd.DataFrame:
    """Create control documentation.

    Args:
        quality_report (QualityReport | dict): The quality control report or its dictionary representation.

    Returns:
        pd.DataFrame: A DataFrame containing control documentation.
    """
    if isinstance(quality_report, dict):
        control_documentation = pd.DataFrame(
            quality_report["control_documentation"]
        ).T.assign(periode=quality_report["data_periode"])
    elif isinstance(quality_report, QualityReport):
        control_documentation = pd.DataFrame(
            quality_report.to_dict()["control_documentation"]
        ).T.assign(periode=quality_report.to_dict()["data_periode"])
    control_documentation.index.names = ["kontroll_id"]
    control_documentation = control_documentation.reset_index()
    return control_documentation


def eimerdb_template(control_documentation: pd.DataFrame) -> list[list[Any]]:
    """Create a template for the EimerDB control table.

    Args:
        control_documentation (pd.DataFrame): The control documentation as a DataFrame.

    Returns:
        list[list[Any]]: A list of lists representing the template for the control table.

    Notes:
        Each entry in the resulting list represents a control, including its period, ID, type, and description.
    """
    controls = []
    for i in control_documentation.to_dict()["control_documentation"]:
        controls.append(
            [
                control_documentation.to_dict()["data_periode"],
                i,
                control_documentation.to_dict()["control_documentation"][i][
                    "kontrolltype"
                ].name,
                control_documentation.to_dict()["control_documentation"][i][
                    "feilbeskrivelse"
                ],
            ]
        )
    return controls
