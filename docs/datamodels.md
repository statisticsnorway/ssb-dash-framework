# Datamodels

Here you find documentation for each datamodel that ssb-dash-framework aims to support.

## Altinn data

This is the default datamodel generated from ssb-altinn-form-tools. It is designed to handle all variations that can occur in altinn3 forms, where nested values can be normalized into a more flat table without losing the hierarchical context.

![Altinn database ERD](datamodels/altinn_datamodel.svg)

| Variable                | Description |
| ----------------------- | ----------- |
| `id`                    | Unique row number |
| `iso_period`            | Period variable in iso-format |
| `skjema`                | Altinn form number (RA-number) |
| `ident`                 | Primary identifier |
| `start_date`            | Start date for the period |
| `end_date`              | End date for the period |
| `skjema_versjon`        | Version of Altinn form |
| `refnr`                 | Unique reference for specific data delivery |
| `kommentar`             | Comment from the form sender |
| `dato_mottatt`          | Date form was received |
| `status`                | Editing status |
| `aktiv`                 | If the delivery is active or should be disregarded |
| `variable`              | Which variable the value is for |
| `verdi`                 | The value of the variable |
| `feltsti`               | Path to the variable in the original nested xml file |
| `feltnavn`              | Name of the variable field in the xml file |
| `alias`                 | Readable name given to replace / supplement the name from the xml file |
| `dybde`                 | How deeply nested the value was in the original xml file |
| `indeks`                | For repeating values, which group the value belongs to |
| `kontaktperson`         | Contact person responsible for the form |
| `epost`                 | Email for the contact person |
| `telefon`               | Phone number for the contact person |
| `bekreftet_kontaktinfo` | If the contact information was confirmed |
| `kommentar_kontaktinfo` | General comment for the form |
| `kommentar_krevende`    | Comment for feedback on the form |

# For maintainers

To create the svg file from the d2 file use:

    nix run nixpkgs#d2 -- --layout=elk -w altinn.d2 altinn_datamodel.svg
