# Hurtigstart

I denne veiledning er målet å sette opp en enkel applikasjon som et utgangspunkt som kan tilpasses til dine behov og bygges videre på.

## Forutsetninger

- Du har grunnleggende kjennskap til Python.
- Du klarer å sette opp en tjeneste i dapla lab som kjører python.
- Du har et ssb-project å jobbe i.

## Steg 1: Klargjøring av prosjekt

Først må du starte opp en tjeneste i dapla lab som du skal jobbe i. Denne tjenesten må inneholde et ssb-project.

Deretter skal du installere pakken ved å følge veiledningen i README.md filen på forsiden til repositoriet [README.md](https://github.com/statisticsnorway/ssb-dash-framework/tree/main).

## Steg 2: Opprett en app.py fil og test at pakken er installert

I prosjektmappen din, opprett en fil som heter `app.py`. Dette er filen der du vil skrive koden for applikasjonen din.

Deretter kan du kopiere og lime inn følgende kode i `app.py` filen din:

```python
import os
from ssb_dash_framework import main_layout
from ssb_dash_framework import app_setup

app = app_setup()

window_list = []

tab_list = []

app.layout = main_layout(window_list, tab_list)

if __name__ == "__main__":
    app.run(
        port=port,
        jupyter_server_url=domain,
        jupyter_mode="tab"
    )
```

Så forsøker du å kjøre denne filen. Du kan gjøre dette ved å åpne filen som en notebook (høyreklikk på filen og velg "Open with" -> "Notebook") og deretter kjøre koden. Hvis alt fungerer som det skal, vil du se en enkel applikasjon som viser en tom side.

## steg 3: Sett opp variabelvelgeren

Nå som du har et oppsett og har bekreftet at rammeverket er installert er det på tide å legge inn litt mer av oppsettet. En sentral del av rammeverket er variabelvelgeren. Dette er en komponent som koordinerer skjermbildene i applikasjonen din og sørger for at alt henger sammen. Du kan finne mer detaljert informasjon om hvordan variabelvelgeren fungerer i docs/explanations/, men det er ikke nødvendig å sette seg inn i for å bruke rammeverket.

Det vi skal gjøre nå er kort fortalt å fortelle rammeverket hvilke variabler vi skal bruke for filtrering og seleksjon slik at dette er tilgjengelig for alle modulene. Du skal ikke legge inn alle variablene i datasettet ditt. Noen slike variabler kan være orgnr, år, variabelnavn, fylke, næringskode og så videre.

```python
from ssb_dash_framework import set_variables

set_variables(["orgnr", "aar"]) # Dette gjør at orgnr og aar er tilgjengelig i applikasjonen din.
start_verdier = { # Valgfritt å ha med, men kan være praktisk for brukervennlighet. Puttes inn i app.layout() funksjonen.
    "orgnr": "971526920",
    "aar": "2020"
}
```

## Steg 4: Legg til moduler

Nå som du har en enkel applikasjon som fungerer, kan du begynne å legge til moduler. Moduler er komponenter i applikasjonen din som gir spesifikke funksjoner eller funksjonalitet.

Som et eksempel skal vi legge til en tabell-modul som heter EditingTable. Denne modulen lar deg se dataene dine i en tabell, og kan også stilles inn for å gjøre det mulig å endre dataene. Denne modulen finnes både som tab og vindu, vi skal legge inn en av hver.

Hvis du har egne data du vil teste med så kan du bruke det, om du ikke har det kan du bruke koden nedenfor for å lage litt eksempeldata:

```python
import pandas as pd
import numpy as np
import pandas as pd

data = {
    'orgnr': ["971526920", "971526920", "971526920", "971526920", "971526920", "971526920",
              "971526920", "971526920", "971526920", "971526920", "971526920", "971526920",
              "972417807", "972417807", "972417807", "972417807", "972417807", "972417807",
              "972417807", "972417807", "972417807", "972417807", "972417807", "972417807"],
    'aar': ["2020", "2020", "2020", "2021", "2021", "2021", "2022", "2022", "2022", "2023", "2023", "2023",
            "2020", "2020", "2020", "2021", "2021", "2021", "2022", "2022", "2022", "2023", "2023", "2023"],
    'variabel': ['ansatte', 'utgifter', 'inntekter'] * 8,
    'verdi': [100, 200, 300, 110, 210, 310, 120, 220, 320, 130, 230, 330,
              105, 205, 305, 115, 215, 315, 125, 225, 325, 135, 235, 335]
}
df = pd.DataFrame(data)
```

For å legge til en modul må du først importere den i `app.py` filen din. Du kan gjøre dette ved å legge til følgende linje øverst i filen:

```python
from ssb_dash_framework import EditingTableTab # Tab modulen
from ssb_dash_framework import EditingTableWindow # Vindu modulen
```

Nå skal vi sette igang med å konfigurere modulen vår. Vi skal lage en tab og et vindu som begge bruker det samme datasettet, men viser litt forskjellig informasjon.

Vi starter med å lage tab modulen. For å gjøre dette må vi starte opp en `EditingTableTab` ved å gi den noen parametere, og legge den inn i tab_list. Her er et eksempel på hvordan du kan gjøre dette:

```python
def get_data_orgnr(orgnr):
    return df[df['orgnr'] == orgnr]

enhetstabell = EditingTableTab(
    label="Enhetstabell",
    inputs=["orgnr"],
    states=[],
    get_data_func=get_data_orgnr,
    ident="aar"
)

tab_list = [
    enhetstabell,
]
```

Nå skal vi sette opp vindu modulen. Prosessen er ganske lik som for tab, men vi skal bruke `EditingTableWindow` i stedet for `EditingTableTab`. Eksempelet nedenfor viser hvordan dette ser ut:

```python
def get_data_aar(year):
    return df[df['aar'] == year]

aars_tabell = EditingTableTab(
    label="Komplett årstabell",
    inputs=["aar"],
    states=[],
    get_data_func=get_data_aar,
    ident="orgnr"
)

window_list = [
    aars_tabell,
]
```

## Steg 5: Kjør applikasjonen

Nå kan du kjøre hele notebooken din og se at du har fått opp en applikasjon med en tab og et vindu.

Koden din burde nå se omtrent slik ut:

```python
import os
from ssb_dash_framework import main_layout
from ssb_dash_framework import app_setup
from ssb_dash_framework import set_variables
from ssb_dash_framework import EditingTableTab # Tab modulen
from ssb_dash_framework import EditingTableWindow # Vindu modulen

import pandas as pd
import numpy as np
data = {
    'orgnr': ["971526920", "971526920", "971526920", "971526920", "971526920", "971526920",
              "972417807", "972417807", "972417807", "972417807", "972417807", "972417807"],
    'aar': ["2020", "2020", "2020", "2021", "2021", "2021", "2022", "2022", "2022", "2023", "2023", "2023"],
    'variabel': ['ansatte', 'utgifter', 'inntekter'] * 4,
    'verdi': [100, 200, 300, 110, 210, 310, 120, 220, 320, 130, 230, 330]
}
df = pd.DataFrame(data)

app = app_setup()

set_variables(["orgnr", "aar"]) # Dette gjør at orgnr og aar er tilgjengelig i applikasjonen din.
default_values = { # Valgfritt å ha med, men kan være praktisk for brukervennlighet. Puttes inn i app.layout() funksjonen.
    "orgnr": "971526920",
    "aar": "2020"
}

def get_data_orgnr(orgnr):
    return df[df['orgnr'] == orgnr]

enhetstabell = EditingTableTab(
    label="Enhetstabell",
    inputs=["orgnr"],
    states=[],
    get_data_func=get_data_orgnr,
    update_table_func=lambda x:x,
    ident="aar"
)

tab_list = [
    enhetstabell,
]

def get_data_aar(year):
    return df[df['aar'] == year]

aars_tabell = EditingTableWindow(
    label="Komplett årstabell",
    inputs=["aar"],
    states=[],
    get_data_func=get_data_aar,
    update_table_func=lambda x:x,
    ident="orgnr"
)

window_list = [
    aars_tabell,
]

app.layout = main_layout(window_list, tab_list, default_values = start_verdier)

if __name__ == "__main__":
    app.run(
        port=port,
        jupyter_server_url=domain,
        jupyter_mode="tab"
    )
```
