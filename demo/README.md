# Demos

In this folder you can find different demos that can be run to see how apps may look when set up.

They are functional and some can be used as a foundation for creating a custom app.

| Demo  | Description |
|-------|------------|
| hello_world    | A very simple example of how to create a module. |
| parqueteditor | Copy paste friendly setup for an app containing the ParquetEditor module. Runnable for SSB-employees using the "dapla-felles-developers" access. |
| altinn_app | DataEditor with custom dataviews for two Altinn forms. Runs standalone on the bundled testdata, no database access needed. |

## altinn_app

```bash
uv run demo/altinn_app/app.py
```

The app seeds a throwaway SQLite database from `ssb_dash_framework_testdata` on every start,
so it runs anywhere. Pick a unit in the variable selector to load a form:

| Form | ident | periode |
|------|-------|---------|
| RA-0187 (monthly) | `12222222`, `12333333` | `2026-01` .. `2026-12` |
| RA-0745 (yearly) | `ATF2134660`, `ATF2134661`, `ATF2134662` | `2024`, `2025`, `2026` |

The RA-0745 view uses `dynamic-list` components to render the repeating groups in the form.
Their `variable` is a SQL `LIKE` pattern, so wildcards are written as `%` and not `*`.

Note that ident `12111111` in `2026-01` has two submissions and will fail to load; see
[docs/known_bugs.md](../docs/known_bugs.md) for that and other rough edges this demo exposes.
