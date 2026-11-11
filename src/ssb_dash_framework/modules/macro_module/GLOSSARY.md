# Macro module

Drilling down from aggregated values to the individual observations behind them, so suspicious units can be investigated in other modules. General terms (Period, Ident, Grouping variable, Value variable, Codelist, Data handler) are defined in [docs/GLOSSARY.md](../../../../docs/GLOSSARY.md).

## Language

**Observation**:
One unit's values for one period, or one repeating group instance's values when the analysis is per instance.
_Avoid_: Row, enhet, micro value

**Comparison period**:
The earlier period that all changes are measured against; by default the period immediately before the selected one.
_Avoid_: Previous year, t-1, fjoråret

**Comparison lag**:
How many periods back the comparison period lies from the selected period.
_Avoid_: Cadence, offset

**Macro table**:
The aggregated view of value variables split by grouping variables, for both the selected and the comparison period.
_Avoid_: Heatmap, heatmap grid, macro view

**Cell**:
One aggregated value in the macro table, defined by a group and a value variable.
_Avoid_: Bucket, field

**Observation list**:
The observations that contribute to a selected cell in either the selected or the comparison period.
_Avoid_: Detail grid, micro table

**Entry**:
An observation that contributes to a cell in the selected period but not in the comparison period.
_Avoid_: Tilgang, new unit

**Exit**:
An observation that contributed to a cell in the comparison period but no longer does in the selected period.
_Avoid_: Avgang, exiter
