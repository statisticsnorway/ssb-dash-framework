# Repeating groups: per-unit sums by default, instance observations on request

An observation is keyed by `ident`, plus an optional `instance` column. The Altinn data handler sums repeating-group values per unit by default, and treats each top-level group instance (e.g. `/NyEngSpredUtsGroup/9`) as its own observation when given `repeating_group`. Values in nested groups are summed into their top-level instance. We chose a key of `ident` (+ `instance`) over only supporting per-unit sums because analysing repeating groups by fields inside the group (e.g. quantity per spreader type) is a common need, and the cost to the module is only a key of one or two columns.

## Consequences

- Instances are matched across periods on their path. If a form renumbers instances between periods, they show as new/gone (`Ny`/`Borte`) rather than changed.
- Summary instances such as `TOTAL_ROW` must be excluded through `exclude_instances`, otherwise they are double counted.
