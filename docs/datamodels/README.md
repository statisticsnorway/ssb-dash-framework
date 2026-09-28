# Datamodels

Here you find documentation for each datamodel that ssb-dash-framework aims to support.

To create the svg file from the dbml file use:

    nix shell nixpkgs#nodejs --command npx --yes @softwaretechnik/dbml-renderer -i docs/datamodels/altinn_datamodel.dbml -o docs/datamodels/altinn_datamodel.svg

## Altinn data

This is the default datamodel generated from ssb-altinn-form-tools.

![Altinn datamodel](/docs/datamodels/altinn_datamodel.svg "Altinn datamodel")
