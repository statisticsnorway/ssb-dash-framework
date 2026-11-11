# Flat macro table instead of a pivot heatmap

The hardcoded version pivots one grouping variable (NACE) into columns, with rows as either value variables or a second grouping variable. The generic macro table is flat instead: one row per combination of the selected grouping variables, followed by an Antall column and one column per value variable. A flat table handles any number of grouping variables with one code path, and every value cell maps directly to a filter (group codes + value variable) for the observation list. Heatmap colouring is kept per value column.

## Consequences

- The hardcoded "count row" becomes an Antall column, and a pinned Totalt row sums all groups.
- Hierarchical codes (e.g. NACE 2/3/4/5 digits, fylke/kommune) are not derived by prefix in the module. Users declare one grouping variable per level, or handle it in their own data handler.
