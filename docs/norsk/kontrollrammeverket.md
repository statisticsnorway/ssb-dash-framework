# Hurtigstart: Kontrollrammeverk

Veiledningen tar utgangspunkt i at du allerede har satt opp en app. Hvis du ikke har det så kan du fortsatt følge beskrivelsen, men du vil måtte sette opp en app for å sjekke at ting er satt opp som det skal. Se hurtigstart.md for veiledning til å sette opp din første app.

Dette dokumentet viser hvordan du bruker kontroller i Editeringsrammeverket. Veiledningen er delt i to biter, hvor den første går gjennom hvordan du bruker det og den andre delen er mer tekniske forklaringer for de som er interessert i den slags.

OBS! Dette rammeverket forutsetter at du har ident og refnr i datasettene dine for at det skal fungere.

## Hvordan bruke kontrollrammeverket

### 1. Importere de nødvendige bitene

Kontrollrammeverket består av to biter, `ControlFrameworkBase` og `register_control`. Det første steget er å hente dette inn i koden din så du kan bruke det videre.

```python
from ssb_dash_framework import ControlFrameworkBase
from ssb_dash_framework import register_control
```

### 2. Sett opp rammen for kontrollene

For å gjøre det enklest mulig å lage et kontrollopplegg som håndterer det aller meste for deg så har vi brukt noen konsepter som er avanserte. Det er ikke nødvendig å forstå for å bruke det, men du kan finne mer tekniske detaljer lenger nede om det er interessant.

Det første steget for å få satt opp rammen er å sette opp det nedenfor, men skift ut "MineEgneKontroller" til noe som passer bedre.

```python
class MineEgneKontroller(ControlFrameworkBase):
    def __init__(
        self,
        time_units,
        applies_to_subset,
        conn,
    ) -> None:
        super().__init__(time_units, applies_to_subset, conn)
```

### 3. Lag kontrollene dine

For å lage kontrollene må vi lage kode som kan plukke ut alle observasjonene i undersøkelsen, om du har en Altinn3 undersøkelse vil det innebære at alle innsendte skjemaer skal sjekkes.

Nedenfor er et eksempel på en kontroll som sjekker etter dublettinnsendinger. Merk at her er det to tidsenheter (time_units), 'aar' og 'kvartal'

```python
class MineEgneKontroller(ControlFrameworkBase):
    def __init__(
        self,
        time_units,
        applies_to_subset,
        conn,
    ) -> None:
        super().__init__(time_units, applies_to_subset, conn)

    @register_control(
        kontrollid="000_dublett",
        kontrolltype="I",
        beskrivelse="Virksomheten har levert flere skjema",
        kontrollerte_variabler=["ident"],
        sorteringsvariabel="",
        sortering="ASC",
    )
    def control_skjema_dublett(self):
        df = self.conn.query("SELECT * FROM skjemamottak")
        # Det nedenfor filtrerer til relevante data ved å filtrere til kun gjeldende tidsperiode og valgt skjema.
        for col, values in self.applies_to_subset.items():
            df = df[df[col].isin(values)]
        # Årsaken til at denne filtreringen fungerer er at self.applies_to_subset er en dictionary bestående av variabelen som skal selekteres på som key, og verdiene som skal plukkes ut som value.
        df["utslag"] = df["ident"].isin(
            df["ident"].value_counts()[lambda x: x > 1].index
        )
        df = df.sort_values("ident")
        df["verdi"] = 0
        return df[
            ["aar", "kvartal", "skjema", "ident", "refnr", "utslag", "verdi"]
        ].drop_duplicates()
```

For at kontrollen din skal fungere er det viktig at det som returneres av koden din er en pandas dataframe med kolonnene "skjema", "ident", "refnr", "utslag" og "verdi". I tillegg må du ha med kolonner for tidsenhetene dine, som i dette tilfellet er "aar" og "kvartal".

Det skal være 1 rad per observasjon (refnr for Altinn3). Utslag kolonnen skal utelukkende inneholde verdiene True og False, hvor True markerer at enheten har slått ut på kontrollen.

Om du studerer koden over kan du et par ting. For eksempel ser du kanskje at at `@register_control` brukes for å legge på litt informasjon (metadata) om kontrollen. Dette brukes i bakgrunnen for å lage en oversikt over kontrollene og legge det inn i databasen din.

Du må fylle inn:

- 'kontrollid' skal være et unikt navn for kontrollen din og brukes i tillegg for å sortere kontrollene i skjermbildet. Her er det ingen formkrav men du kan bruke nummerering i navnet for å få rammeverket til å sortere de i rekkefølgen du ønsker. I eksempelet over starter id-en på '000' for å sikre at den er øverst.
- 'kontrolltype' skal være en av tre verdier. "I" for informative kontroller, altså de som er til orientering. "S" betyr at det er en myk kontroll (soft control) og skal brukes der kontrollen signaliserer en mulig feil som skal undersøkes. "H" brukes for å markere harde kontroller (Hard control) som viser at det er en absolutt feil i dataene.
- 'beskrivelse' bruker du for å legge inn en forklaring på hva kontrollen sjekker og hvorfor.
- 'kontrollerte_variabler' skal liste opp hvilke variabler som er relevante for kontrollen. Her kan det være så mange variabler som du ønsker.
- 'sorteringsvariabel' brukes for å si noe om hvilken variabel utslagene skal sorteres etter. Om du for eksempel ønsker å se enheten med størst verdi på omsetning øverst i listen setter du "omsetning" her.
- 'sortering' angir om du skal ha sorteringen stigende (ASC) eller synkende (DESC).

Du ser kanskje også at det er innrykk på koden for kontrollen. Det er for å fortelle python at `control_skjema_dublett` skal ses på som en del av `MineEgneKontroller` classen, som gjør at vi i bakgrunnen kan automatisere en del prosesser. Mer forklaring kan du finne i andre del av veiledningen om du er interessert.

Det er lagt til en del validering av resultatene som kontrollkoden din lager, men den gjøres ikke før du forsøker å kjøre koden gjennom rammeverket. Det kan være lurt å lage en kontroll og få den til å fungere før du går videre og lager flere.

### 4. Legg inn modulen i applikasjonen din

Da er vi på det et siste steget før det burde fungere, og det er å legge det inn i selve applikasjonen.

```python
from ssb_dash_framework import ControlViewWindow

kontrollvindu = ControlViewWindow(
    time_units=["aar", "kvartal"],
    control_dict={"RA-XXXX": MineEgneKontroller}, # Sett inn ditt skjemanummer og kontrollklassen som gjelder for skjemaet her.
    conn=conn,
)
```

### 5. Noen anbefalinger

- Lag en egen .py fil som inneholder kontrollene dine, det blir mer oversiktlig. Se https://github.com/statisticsnorway/demo-ssb-dash-framework/tree/parquet-editor-demo/demos/altinn3 for eksempel.

## Teknisk forklaring - valgfri lesning

Her går vi gjennom noe mer av logikken bak, gjerne se i selve koden om du vil se hvordan opplegget helt konkret fungerer.

### Prosessen som settes igang når kontroller kjøres



### Inheritance (arv)
