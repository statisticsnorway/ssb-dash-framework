from abc import abstractmethod
from typing import Any

from .microlayout_components.editable_field_model import FieldCallbackContainer
from ..sidebar.meta import SidebarMeta


class MicrolayoutMeta[T](SidebarMeta):
    """Unified data retrieval interface specifying database actions for microlayout form widgets."""

    @abstractmethod
    def get_field(
        self,
        settings: T,
        container: FieldCallbackContainer,
        inputs: list[Any] | dict[Any, Any],
    ) -> Any:
        """Retrieves the value of a specific field from the database.

        Args:
            settings: Active editor configuration settings.
            container: The callback metadata wrapper containing the field settings.
            inputs: State and inputs wired into the field trigger callbacks.

        Returns:
            The field value retrieved from the database.
        """
        ...

    @abstractmethod
    def update_field_value(
        self,
        refnr: str,
        skjema: str | None,
        ident: str,
        period: str,
        value: Any,
        old_value: Any,
        settings: T,
        container: FieldCallbackContainer,
        inputs: list[Any] | dict[Any, Any],
        editing_code: str | None,
    ) -> Any:
        """Updates the database value of a specific field.

        Args:
            refnr: Reference number.
            skjema: Questionnaire schema name.
            ident: Respondent identifier.
            period: Statistical period.
            value: The new updated value.
            old_value: The previous field value.
            settings: Active editor configuration settings.
            container: The callback metadata wrapper containing the field settings.
            inputs: Wired input states.
            editing_code: Selected editing reason code.

        Returns:
            The result of the database write operation.
        """
        ...

    @abstractmethod
    def get_timeseries(
        self,
        settings: T,
        variable: str | list[str],
        refnr: str,
        ident: str,
        periods: list[str],
    ) -> list[dict]:
        """Retrieves historical values of target variables over multiple periods.

        Args:
            settings: Active editor configuration settings.
            variable: Target field name path(s).
            refnr: Reference number.
            ident: Respondent identifier.
            periods: List of previous statistical periods to fetch.

        Returns:
            A list of dictionary records mapping periods to values.
        """
        ...

    @abstractmethod
    def get_dynamic_list(
        self,
        settings: T,
        wildcard: str,
        refnr: str,
    ) -> list[dict]:
        """Queries dynamic list entries matching a wildcard field pattern.

        Args:
            settings: Active editor configuration settings.
            wildcard: Slashed path search pattern (e.g. `/sub_units/*`).
            refnr: Reference number.

        Returns:
            A list of dictionary records representing row values.
        """
        ...
