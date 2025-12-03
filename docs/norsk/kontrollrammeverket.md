
# Hurtigstart: Kontrollrammeverk

Dette dokumentet viser hvordan du bruker og utvider kontrollrammeverket for SSB sine datasett.
Ikke endelig. Jeg skal kvalitetssikre og finpusse etter feriedagene mine.

## Struktur og bruk

Kontrollrammeverket består av en baseklasse `ControlFrameworkBase` og én eller flere kontrollklasser som arver fra denne. Du må lage en egen klasse som arver fra baseklassen, og i denne klassen lager du kontrollmetoder. Alle kontrollmetoder må starte med `control_`.

### 1. Kontrollrammeverket og baseklassen

Kontrollrammeverket er bygd opp rundt en baseklasse `ControlFrameworkBase`, som inneholder funksjonalitet for å:
- kjøre alle kontroller du har definert i klassen din,
- finne nye eller endrede kontrollutslag,
- laste inn disse i databasen.

**Du skal ikke opprette en instans av `ControlFrameworkBase` direkte.** Du lager din egen kontrollklasse som arver fra baseklassen. Kontrollklassen er stedet der du definerer selve kontrollene.

Eksempel:
```python
class RA0657Controls(ControlFrameworkBase):
    def __init__(self, partitions, partitions_skjema, conn):
        super().__init__(partitions, partitions_skjema, conn)
```

I kontrollklassen definerer du kontrollmetoder som starter med `control_`. Rammeverket vil automatisk oppdage og kjøre disse metodene når du bruker `insert_new_rows()` eller `execute_controls()`.

#### Viktige metoder i baseklassen:

- `_run_all_controls()`: Kjører alle metoder i klassen som begynner med `control_`
- `_control_new_rows()`: Sammenligner nye kontrollutslag med det som allerede ligger i databasen, og returnerer kun nye rader
- `insert_new_rows()`: Detekterer nyinnlastede skjemaer. Laster inn nye kontrollutslag tilhørende de nye skjemaene.
- `_control_updates()`: Ser etter oppdateringer i eksisterende rader
- `execute_controls()`: Oppdaterer databasen med nye utslag dersom utslagsbetingelsen har endret seg

### 2. Registrering av kontroller i databasen

Før en kontroll kan brukes i rammeverket, må den også registreres som en rad i kontroller-tabellen i databasen.
Eksempel på registrering:

```python
import eimerdb as db
import pandas as pd

conn = db.EimerDBInstance("ssb-strukt-naering-data-europe-west4-prod", "svalbardbasen")

# Kontrollmetadata
kontrollinfo = {
    "aar": 2023,
    "skjema": "RA-0657",
    "kontrollid": "T001",
    "type": "test",
    "beskrivelse": "Totale kostnader større enn total omsetning!",
    "kontrollvar": "diff",
    "varsort": "DESC"
}

# Opprett DataFrame og sett inn i tabellen
conn.insert("kontroller", pd.DataFrame(kontrollinfo, index=[0]))

```

Variabelen kontrollvar angir hvilken variabel som skal kunne brukes til sortering og visning i kontrollappen – for eksempel et avvik eller en differanseverdi.
Feltet varsort bestemmer rekkefølgen på sorteringen: enten "DESC" for synkende eller "ASC" for stigende.

Når raden er lagt inn i tabellen kontroller, vil kontrollen automatisk bli fanget opp av kontrollrammeverket.

### 3. Slik lager du en kontrollklasse

Du må lage en egen klasse for hvert skjema du ønsker å kontrollere. Denne klassen skal:
- arve fra `ControlFrameworkBase`,
- kalle `super().__init__()` i `__init__`-metoden,
- inneholde én eller flere metoder som starter med `control_`.

Hver kontrollmetode må returnere en `pandas.DataFrame` med følgende kolonner:
- `aar` (Flere tidsperioder er mulig)
- `skjema`
- `ident`
- `refnr`
- `kontrollid`
- `utslag` (True/False)
- `verdi` (valgfri tallverdi som kontrollen er basert på)

Eksempel på kontrollmetode:
```python
def control_V001(self):
    ...
    return df_output
```

```python
kontrollerclass = RA0657Controls(
    partitions={"aar": ["2024"]},
    partitions_skjema={"aar": ["2024"], "skjema": ["RA-0657"]},
    conn=conn
)

kontrollerclass.insert_new_rows()     # Laster inn nye rader
kontrollerclass.execute_controls()    # Oppdaterer eksisterende rader
```

## Format for kontrollutslag

Alle kontrollmetoder skal returnere en DataFrame med følgende kolonner:
- `aar`: årstall (int) (Flere tidsperioder er mulig)
- `skjema`: skjemanavn (str)
- `ident`: identifikator (str/int)
- `refnr`: versjon (str/int)
- `kontrollid`: ID for kontrollen (str, f.eks. "V001")
- `utslag`: bool (True/False)
- `verdi`: int/float – verdien som brukes i kontrollen

## Bruk i app-modulen

Lag et dictionary med en entry for hvert skjema, der key = RA-nummeret og value = klassen.

```python
control_dict = {"RA-0657": RA0657Controls}
kontrollvindu = AltinnControlModal(time_units=["aar"], control_dict, conn)
```

Deretter legger du inn kontrollmodalen i lista med vinduer som går inn i main_layout
