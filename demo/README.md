# Demos

In this folder you can find different demos that can be run to see how apps may look when set up.

They are functional and some can be used as a foundation for creating a custom app.

| Demo  | Description |
|-------|------------|
| hello_world    | A very simple example of how to create a module. |
| getting_started | The finished app from the [getting started guide](../docs/guides/getting_started.md). Runs anywhere, no data access needed. |
| hb_method | Runs `HBMethod` with the Altinn data handler, bundled SQLite test data, and the framework `DataEditor`. |
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

## hb_method

```bash
uv run demo/hb_method/app.py
```

The demo loads the bundled Altinn test data into process-local in-memory SQLite,
then uses `AltinnHBDataHandler` and the real Vaskify flow. It adds a deterministic
HB outlier so the result has a known flagged unit. Click that unit to select it,
switch to **Data editor**, and edit the field labelled **Areal ny eng (dekar) -
demo-data**. Click **Lagre redigering** to open the reason-and-justification
dialog; the value is saved only after confirmation. Return to **HB metoden** and
run it again to see the updated result. The edited value and demo edit history
exist only in memory and disappear when the app exits; the bundled fixture and
production data are never changed. Changing the selected unit or period reloads
the editor for that submission and discards any pending edit, so it cannot be
saved against a different selection.


## For contributors
