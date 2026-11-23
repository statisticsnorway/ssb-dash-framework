HB methodology module
=====================

``HBMethod`` connects the framework's shared selectors and an HB data handler
to Vaskify's Hidiroglou-Berthelot method. The module reads the selected
variable and period, requests the corresponding data from the handler, and
displays the result. Source retrieval and HB calculation remain separate
responsibilities.

Configure the module
--------------------

Configure the framework's shared data connection before running the app. The
Altinn handler uses that connection to read the ``enheter``, ``skjemamottak``,
and ``skjemadata`` tables. Choose the connection function for your backend; the
example below uses ParquEdit.

.. code-block:: python

   from ssb_dash_framework import (
       HBMethod,
       VariableSelectorConfig,
       VariableSelectorOption,
       set_parquedit_connection,
   )
   from ssb_dash_framework.modules.hb import AltinnHBDataHandler
   from ssb_dash_framework.setup.variableselector import TimeUnit
   from ssb_dash_framework.setup.variableselector import TimeUnitType

   set_parquedit_connection()

   hb_time_unit = TimeUnit(name="periode", frequency=TimeUnitType.YEAR)
   VariableSelectorConfig(
       refnr="refnr",
       ident="ident",
       time_units=hb_time_unit,
       grouping_variables=["altinnskjema"],
   )
   VariableSelectorOption("measure")

   hb_method = HBMethod(
       hb_data_handler=AltinnHBDataHandler(
           configured_hb_form="RA-0745",
           hb_variable_to_feltsti={
               "new_grass_area": "/NyEngArbAreal",
           },
       ),
       hb_variable_selector="measure",
       configured_hb_time_unit=hb_time_unit,
   )

Replace the example form and field path with values from the target Altinn
schema. ``configured_hb_form`` is the form identifier.
``hb_variable_to_feltsti`` maps each selectable HB variable value to its exact
Altinn field path (``feltsti``). Its keys must match the values supplied by the
variable selector; ``hb_variable_selector`` is the selector's configured
title. The map must cover every selectable HB variable. If
``configured_hb_strata_variable`` is set on ``HBMethod``, its value must also
have a field-path mapping.

For each comparison period, the handler selects the latest active submission
for each unit separately. If multiple answers match the configured measure
``feltsti`` in that submission, the handler does not choose or aggregate them:
it leaves the value missing and returns a warning. The module displays an
aggregate warning count, not the affected unit-period details. A configured
strata field must have exactly one non-null, non-blank matching answer for each
unit-period; a missing or ambiguous strata answer stops the run rather than
silently switching to an unstratified calculation. See the
`Altinn data-selection notes <https://github.com/statisticsnorway/ssb-dash-framework/blob/main/altinnapiclient-documentation.md>`_
for the detailed selection rules.

``AltinnHBDataHandler`` requires the app's shared connection to be configured;
it does not create a connection of its own. For other backends, use the
framework connection setup described in the
`data connection guide <https://github.com/statisticsnorway/ssb-dash-framework/blob/main/docs/guides/connecting_to_data.md>`_.
The handler requires the Altinn data model tables named above. See the
`runnable HB example <https://github.com/statisticsnorway/ssb-dash-framework/blob/main/demo/hb_method/app.py>`_
for the complete app setup.

The module registry does not construct ``HBDataHandlerMeta`` or ``TimeUnit``
instances from YAML mappings. Create these Python objects in the app and inject
them into ``HBMethod`` as shown above.

The source is replaceable: an alternative handler can implement
``HBDataHandlerMeta`` and return an ``HBDataResult``. This keeps ``HBMethod``
independent of Altinn and permits prepared DataFrames or other data sources.

Common HB DataFrame contract
----------------------------

The handler returns one row per unit and period for the requested comparison
pair. The required columns are:

.. list-table::
   :header-rows: 1

   * - Column
     - Contract
   * - ``unit_id``
     - Non-empty string identifying the unit consistently across both periods.
   * - ``period``
     - Non-empty canonical period string for the configured frequency.
   * - ``value``
     - Numeric pandas column; missing values are allowed.

``unit_id``/``period`` pairs must be unique. ``strata`` is optional unless a
stratification variable is configured; when used, the handler supplies the
normalized ``strata`` column with a consistent stratum for each unit across
both periods. Data handlers may return structured, non-fatal warnings with the
DataFrame.

The common data contract accepts these canonical period strings for the six
``TimeUnit`` frequencies:

.. list-table::
   :header-rows: 1

   * - Frequency
     - Canonical form
     - Example
   * - Year
     - ``YYYY``
     - ``2025``
   * - Half-year
     - ``YYYY-1`` or ``YYYY-2``
     - ``2025-2``
   * - Quarter
     - ``YYYY-Q1`` through ``YYYY-Q4``
     - ``2025-Q3``
   * - Month
     - ``YYYY-MM``
     - ``2025-08``
   * - Week
     - ``YYYY-Www`` (valid ISO week)
     - ``2025-W01``
   * - Day
     - ``YYYY-MM-DD`` (valid calendar date)
     - ``2025-08-31``

These formats define valid HB input; they do not guarantee that the current
Vaskify version can run every frequency. ``HALF_YEAR`` comparisons are
currently disabled because Vaskify rejects ``YYYY-1`` and ``YYYY-2`` periods.

Every period must match the configured frequency. Return only the two periods
requested by the handler call, with at most one row per unit in each period.

Comparison-period assumption
----------------------------

The selected period is ``t``. The module derives ``t-1`` by subtracting one
unit using the configured ``TimeUnit``, and compares ``(t-1, t)``. For example,
``2025-Q1`` compares with ``2024-Q4``. This means the comparison uses the
previous period at the same frequency; it does not search for the previous
period that happens to have data. The handler must be able to provide both
periods.

Results and limitations
-----------------------

The module delegates HB calculation to Vaskify. The current call uses
``p_u=0.5``, ``p_a=0.05``, ``p_c=20``, and the 25th and 75th percentiles; these
parameters are fixed in the module, not user-editable. They are integration
defaults, not a claim that one calibration is appropriate for every group or
comparison period; parameter choices require methodology approval.

The result plot shows the value in selected period ``t`` against Vaskify's
returned ratio. It also shows the returned median ratio and lower and upper
limits for each stratum. The framework displays these diagnostics but does not
recalculate them.

.. list-table::
   :header-rows: 1

   * - ``flag_hb``
     - Interpretation
   * - ``1``
     - Flagged candidate; the ratio is outside the calculated limits.
   * - ``0``
     - Evaluated and not flagged.
   * - Missing
     - Not comparable; no HB diagnostic was produced for the unit.

Only units with positive values in both periods participate in the HB
calculation. Units with a missing, zero, or negative value are retained in the
normalized result but have no HB flag. A flag is a screening signal for
statistical review, not a conclusion that a value is erroneous. When strata
are configured, Vaskify calculates the reference distribution within each
stratum. If no units are eligible, Vaskify returns no diagnostics and the
module treats the run as a failure, not as a successful result with no flagged
units.

HB runs automatically on first entry when the required selections are
available. The **Kjør HB-metoden** button remains available for a manual rerun.
After data is edited and saved elsewhere, the existing HB result does not
currently receive a save-completed signal; rerun the method before
interpreting results as reflecting those edits. This refresh limitation is
tracked as ``HB-METHOD-RESULT-REFRESH-001``.

Interaction and write boundary
------------------------------

Clicking a plotted unit updates the shared ``VariableSelector`` identifier
using the stable ``unit_id``. This lets other modules, such as the Data Editor,
follow the selected unit; clicking does not rerun HB. The click does not modify
data or persist a value.
``HBMethod`` reads and analyzes data only; editing, saving, and audit handling
belong to the Data Editor or the configured source integration.
