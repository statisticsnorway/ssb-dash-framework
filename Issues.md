# Issues

| ID | Area | Bug | Observed behavior | Impact / planned handling | Status |
|---|---|---|---|---|---|
| HB-PERIOD-001 | `TimeUnit.parse()` / WEEK | Canonical week periods cannot be parsed. | Parsing `2024-W01` raises `ValueError: Unsupported token: WW` with the installed Pendulum version. | Resolve as part of period resolution and add regression coverage for valid and invalid ISO week periods. | Open |
| HB-PERIOD-002 | `SelectedTimeUnit.to_str()` / QUARTER | Quarter periods are not formatted canonically. | A selected `2024-Q1` formats as `2024-11`; the previous quarter from that value formats as `2023-44`. | Resolve as part of period resolution and add regression coverage for canonical quarter output and year rollover. | Open |
