# Vaskify HB API: oppførsel og datakontrakt

Dette dokumentet samler kjente fakta om Vaskifys offentlige HB-grensesnitt og
hvordan det forholder seg til HB-modulen i SSB Dash Framework. Det beskriver
observerte API-kontrakter og begrensninger; det er ikke en implementeringsplan
eller et sett med instrukser til en agent.

## Felles DataFrame-format

Frameworkets eksisterende `HBDataHandlerMeta`-kontrakt beskriver en
pandas-DataFrame med én rad per enhet og periode, og disse obligatoriske
kolonnene:

| Kolonne | Gjeldende kontrakt |
|---|---|
| `unit_id` | Ikke-tom tekstlig enhetsidentifikator. |
| `period` | Kanonisk periode som tekst, for eksempel `2024`, `2024-Q1` eller `2024-01`. |
| `value` | Numerisk verdi. Manglende verdier er tillatt; boolske verdier er ikke gyldige. |

Den tilhørende validatoren kontrollerer at input er en pandas-DataFrame, at
kolonnenavnene ikke er dupliserte, at obligatoriske kolonner finnes, at
`unit_id` og `period` består av ikke-tomme strenger, at perioden er år,
kvartal eller måned, at `value` har numerisk dtype, og at det maksimalt
finnes én rad per `unit_id`/`period`. Manglende `value` er tillatt.

Vaskifys lange-format-konvertering bruker `pivot_table` med
`aggfunc="first"`. Duplikate enhet/periode-rader kan derfor bli slått sammen
ved konvertering i stedet for å gi en tydelig duplikatfeil.

Ekstra kolonner kan finnes for strata eller kontekst som skal beholdes for
`VariableSelector`. De er ikke automatisk del av Vaskifys HB-inndata.

## Perioder i HB-kallet

HB-funksjonen sammenligner to perioder. I langt format tar Vaskifys
`time_periods`-argument en liste med periodene som skal sammenlignes.
Vaskify utleder ikke et foregående tidsrom fra en valgt periode; periodene
følger med i kallet. Hvis `time_periods` ikke oppgis, forventer
langformatimplementasjonen at tidskolonnen inneholder nøyaktig to unike
perioder.

## Vaskifys offentlige HB-grensesnitt

Vaskify eksponerer HB gjennom `Detect.hb()`. Den observerte signaturen er:

```python
def hb(
    self,
    y_var: str | list[str],
    time_var: str | None = None,
    time_periods: list[str] | None = None,
    strata_var: str = "",
    pu: float = 0.5,
    pa: float = 0.05,
    pc: float = 20,
    percentiles: tuple[float, float] = (0.25, 0.75),
    flag: str = "flag_hb",
    output_format: str = "wide",
    output_scope: str = "all",
) -> pandas.DataFrame:
    ...
```

Eksempel for det lange DataFrame-format som brukes av frameworkets HB-kontrakt:

```python
from vaskify import Detect

detector = Detect(hb_input_dataframe, id_nr="unit_id")
hb_vaskify_result_dataframe = detector.hb(
    y_var="value",
    time_var="period",
    time_periods=list(hb_comparison_periods),
    strata_var="strata" if configured_hb_strata_variable else "",
    output_format="wide",
    output_scope="all",
)
```

Vaskify har interne metoder som `_hb_long()`, `_hb_wide()` og
`_calculate_hb()`. De er implementasjonsdetaljer, ikke del av det offentlige
API-et.

### Parametere og standardverdier

| Parameter | Standard | Beskrivelse i Vaskify |
|---|---:|---|
| `pu` | `0.5` | Justering for nivåforskjeller mellom variablene. |
| `pa` | `0.05` | Justering knyttet til median og kvartiler. |
| `pc` | `20` | Kontrollerer bredden på grensene. |
| `percentiles` | `(0.25, 0.75)` | Kvantilene som brukes. |
| `flag` | `"flag_hb"` | Navn på utfallsflagget. |
| `output_format` | `"wide"` | Formatet på resultatet. |
| `output_scope` | `"all"` | Returnerer alle enheter eller bare uteliggere. |

HB-metoden dokumenterer ingen eksplisitt validering av parametergrensene for
`pu`, `pa`, `pc` eller `percentiles`.

### Inputformater

Langt format bruker tekst for `y_var` og en tidskolonne:

```python
y_var="value"
time_var="period"
time_periods=["2023", "2024"]
```

Bredt format bruker en liste med to verdikolonner og `time_var=None`:

```python
y_var=["value_2023", "value_2024"]
time_var=None
```

Standard `output_format` er `"wide"`. Vaskify støtter parameterverdiene
`"wide"`, `"long"` og `"infer"`; begrensningene ved ugyldige valg beskrives
under.

## Valideringer og meldinger

Feilmeldingene er tekniske API-meldinger. `Detect`/`_check_data()` reiser
`ValueError` for følgende observerte kontroller:

| Tilstand | Melding |
|---|---|
| Manglende kolonne | `Missing column: <kolonnenavn>` |
| ID-kolonnen har ikke godkjent string-dtype | `<id_nr> should be a string.` |
| Målvariabelen er ikke numerisk | `<y_var> should be numeric.` |
| Tidskolonnen har ikke string-dtype | `<time_var> should be a string.` |
| Tidsverdier matcher ikke et støttet format | `<time_var> should be in the format 'YYYY', 'YYYY-Qq', 'YYYY-MM','YYYY-Www','YYYY-MM-DD', 'YYYY-DDD'.` |

Vaskifys datokontroll er mønsterbasert. Den sjekker ikke om en dato er en
reell kalenderdato. Vaskifys mønstre omfatter år, måned, dag, kvartal,
ISO-uke og ordinaldato; frameworkets felles HB-kontrakt begrenser perioder
til år, kvartal og måned.

Flere HB-situasjoner logger `error` eller `warning` uten nødvendigvis å kaste
et unntak:

| Situasjon | Logg eller observert oppførsel |
|---|---|
| `time_periods` har et annet antall enn to | Logger `Two time periods should be specified.` og fortsetter. |
| Filtrerte inndata har noe annet enn to unike perioder | Logger `The time variable must have exactly two unique levels.`; senere kode kan feile når periodene brukes. |
| Feil type `y_var` for inputformen | Logger `y_var must contain a list with two column names for wide format.` eller `y_var must contain a string with column name for long format.` og fortsetter. |
| Feil antall kolonner i bred form | Logger at nøyaktig to kolonnenavn kreves; for få kolonner kan gi indeksfeil, flere kolonner enn to kan bli ignorert. |
| Ingen rader har positive verdier i begge perioder | Filtrerer bort rader med verdi `<= 0`; logger `No valid rows with y_var > 0 for both time periods.` når ingen rader står igjen, men fortsetter. |
| Ugyldig `output_format` | Logger `output_format is not valid. Use 'wide', 'long' or 'infer'. Returning 'wide' format.`. Koden setter ikke variabelen til `"wide"` i denne grenen. |
| `output_format="long"` med bred inndata | Logger at bare bredt output er tilgjengelig og fortsetter med bredt output. |
| Ukjent `output_scope` | Valideres ikke; bare verdien `"outliers"` aktiverer filtrering. |
| Manglende strata-kolonne | Kolonnen sjekkes ikke eksplisitt av `_check_data()` før gruppering. |

## Resultat og flagg

Med `output_format="wide"` inneholder resultatet normalt én rad per enhet,
verdikolonner for sammenligningsperiodene og metodens diagnostikk. De
observerte HB-resultatkolonnene er:

```text
ratio
median_ratio
lower_limit
upper_limit
flag_hb
```

Når `strata_var` er satt, beregnes grenser separat per strata.

| Flagg | Betydning |
|---|---|
| `1` | Flagget som mulig uteligger av HB-metoden. |
| `0` | Beregnet og ikke flagget. |
| Manglende | Ingen beregnet diagnostikk / ikke sammenlignbar; ikke lik `0`. |

HB-beregningen bruker bare observasjoner med positive verdier i begge
periodene. Nullverdier, negative verdier og manglende verdier får derfor ikke
vanlig beregnet HB-diagnostikk. Et fravær av flaggede rader er forskjellig fra
et fravær av sammenlignbare rader.
