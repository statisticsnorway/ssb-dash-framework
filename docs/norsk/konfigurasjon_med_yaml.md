# Konfigurasjon av appen med yaml filer

Obs! Ny funksjonalitet så dette kan være litt ustabilt.

## Støttede moduler

- Variabelvelger
- DataViewCustom

## Hva er yaml og hvorfor bruke yaml?

Yaml er laget for å være lesbart for mennesker og kompatibelt på tvers av kodespråk og systemer, i tillegg er det svært vanlig så det er godt dokumentert med mye eksempler.


[Mer informasjon om yaml kan du finne her](https://yaml.org/about/)

[En oversikt over yaml syntaks kan du finne her](https://yaml.com/resources/cheatsheet/#anchors-aliases)

## Hvordan sette opp?

Generelt vil layout (det grafiske oppsettet) skrives i yaml filen med et spesifikt mønster.

```yaml
- type: row
  children:
  - type: col
    children:
    - type: modul
      ...
```

I oppsettet over markerer man et nytt element med "-", og deretter må man si hvilken type dette skal være (row, col og modul i eksempelet).

For generelle oppstillings-typer som rad (row) og kolonne (col) forventer ssb-dash-framework at du også definerer "children" med underliggende elementer. På denne måten kan du definere et "rutenett" av kolonner og rader som moduler og komponenter kan settes inni.

!Må finne ut hvordan modul-spesifikk konfigurasjon skal dokumenteres!

### DataViewCustom

Skreddersydde visninger for spesifikke skjemaer og spesifikke tabeller kan skrives med yaml filer.

En fordel med denne tilnærmingen er at oppsettet blir mindre sårbart for breaking changes, du trenger ikke kodekompetanse for å sette opp eller vedlikeholde visningen og det blir ofte lettere å lese.

[Eksempelfil fra demo](../../demo/dataeditor_yaml_based/data_view_custom.yaml)

!Sett inn bilde her!

