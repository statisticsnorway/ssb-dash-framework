
# Hurtigstart: Kontrollrammeverk

Dette dokumentet viser hvordan du bruker kontroller i Editeringsrammeverket.

OBS! Dette rammeverket forutsetter at du har ident og refnr i datasettene dine,. MÅ FORKLARES BEDRE

## Bruk

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

Nedenfor er et eksempel på en kontroll som sjekker etter dublettinnsendinger.

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
        df["utslag"] = df["ident"].isin(
            df["ident"].value_counts()[lambda x: x > 1].index
        )
        df = df.sort_values("ident")
        df["kontrollid"] = "skjema_dublett"
        df["verdi"] = 0
        return df[
            ["aar", "kvartal", "skjema", "ident", "refnr", "kontrollid", "utslag", "verdi"]
        ].drop_duplicates()
```

For at kontrollen din skal fungere er det viktig at det som returneres av koden din er en pandas dataframe med kolonnene "aar", "kvartal", "skjema", "ident", "refnr", "kontrollid", "utslag" og "verdi". Det skal være 1 rad per observasjon (refnr for Altinn3). Utslag kolonnen skal utelukkende inneholde verdier som True eller False, hvor True markerer at enheten har slått ut på kontrollen.

Om du studerer koden over kan du et par ting. For eksempel ser du kanskje at at `@register_control` brukes for å legge på litt informasjon (metadata) om kontrollen. Dette brukes i bakgrunnen for å lage en oversikt over kontrollene og legge det inn i databasen din.

Du ser kanskje at det er innrykk på koden for kontrollen. Det er for å fortelle python at `control_skjema_dublett` skal ses på som en del av `MineEgneKontroller` classen, som gjør at vi i bakgrunnen kan automatisere en del prosesser.



### 4. Legg inn modulen i applikasjonen din

Da er det et siste steg igjen før det burde fungere, og det er å legge det inn i selve applikasjonen.

```python
from ssb_dash_framework import AltinnControlViewWindow

kontrollvindu = AltinnControlViewWindow(
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

