"""Provide normalized HB data from the configured Altinn source."""

from collections.abc import Mapping

from .altinn_candidate_retrieval import AltinnHBCandidateRetriever
from .altinn_normalization import normalize_altinn_hb_candidate_records
from .data_handler import HBDataHandlerMeta
from .data_handler import HBDataResult


class AltinnHBDataHandler(HBDataHandlerMeta):
    """Retrieve, select, and normalize Altinn records for an HB run."""

    def __init__(
        self,
        *,
        configured_hb_form: str,
        hb_variable_to_feltsti: Mapping[str, str],
    ) -> None:
        """Configure the Altinn form and exact path for each HB variable."""
        self._candidate_retriever = AltinnHBCandidateRetriever(
            configured_hb_form=configured_hb_form,
            hb_variable_to_feltsti=hb_variable_to_feltsti,
        )

    def get_hb_dataframe(
        self,
        *,
        selected_hb_variable: str,
        hb_comparison_periods: tuple[str, str],
        configured_hb_strata_variable: str | None = None,
    ) -> HBDataResult:
        """Return normalized unstratified HB data and source warnings.

        Raises:
            NotImplementedError: If a strata variable is requested.
            ValueError: If the selected variable or comparison periods are
                invalid, or an active submission is missing.
        """
        if configured_hb_strata_variable is not None:
            raise NotImplementedError(
                "AltinnHBDataHandler does not support a configured strata variable."
            )

        candidate_records = self._candidate_retriever.retrieve_candidate_records(
            selected_hb_variable=selected_hb_variable,
            hb_comparison_periods=hb_comparison_periods,
        )
        selected_active_candidate_records = (
            self._candidate_retriever.select_active_candidate_records(
                candidate_records,
                hb_comparison_periods=hb_comparison_periods,
            )
        )
        self._candidate_retriever.validate_active_submission_coverage(
            candidate_records,
            selected_active_candidate_records,
        )

        selected_feltsti = self._candidate_retriever.get_feltsti_for_hb_variable(
            selected_hb_variable
        )
        return normalize_altinn_hb_candidate_records(
            selected_active_candidate_records,
            selected_feltsti=selected_feltsti,
        )
