# Variabelvelgeren (VariableSelector)

Her vil det være en enkel gjennomgang av variabelvelgeren, for en mer detaljert forklaring kan du se i "docs/explanations" mappen.

## Hva er variabelvelgeren og hva gjør den?

Når du bygger en applikasjon har du gjerne flere moduler / visninger. Kanskje du har et kart som viser data for et bestemt år, og en tabell som viser detaljer for det samme året.

Hvis du vil se data for et annet år må både kartet og tabellen oppdateres, og det er her variabelvelgeren kommer inn i bildet.

Når du endrer en verdi i Variabelvelgeren (f.eks. bytter fra år 2022 til 2023), sendes den nye informasjonen automatisk ut til alle moduler som "abonnerer" på den. Dette sikrer at alle deler av applikasjonen jobber med de samme, oppdaterte dataene. Det er litt som hvordan en dirigent sørger for at hele orkesteret spiller i samme takt og toneart – Variabelvelgeren dirigerer dataflyten i applikasjonen din.

Uten en slik sentralisert mekanisme, måtte hver modul kommunisert med hverandre direkte, noe som fort kan bli komplisert og feilutsatt, spesielt i større applikasjoner.

## Hvordan brukes den?

Først må du definere hvilke variabler applikasjonen din trenger som nedenfor. Rekkefølgen her bestemmer rekkefølgen i sidepanelet.

```python
from ssb_dash_framework import set_variables

set_variables(["ident", "aar", "maaned", "kommune", "variabel"])
```

Dette gjør at verdiene blir tilgjengelige for moduler du vil sette opp i appen din.

Når du setter opp en modul i appen din så vil modulen ofte trenge en liste over "inputs" og "states".

```python
from ssb_dash_framework import EditingTableTab
min_modul = EditingTableTab(
    label="Min tabell",
    inputs=["kommune"],
    states=["aar", "maaned"],
    get_data_func=min_funksjon,
)
```

Inputs sier at modulen skal oppdateres hvis en av disse variabelverdiene endres. I eksempelet over vil tabellen oppdateres hvis 'kommune' endres i variabelvelgeren.

States derimot fører ikke til en oppdatering i modulen, men modulen gjør "oppslag" på de variabelverdiene når den oppdaterer seg. Så hvis 'aar' endres vil ikke det føre til at tabellen oppdateres, men når en oppdatering skjer så vil den sjekke verdien til 'aar'.

Om du ikke ønsker å inkludere states kan du skrive `states = []` istedenfor å gi den variabler.

## Hvordan fungerer den?

Dette avsnittet gir en kort forklaring om hvordan den fungerer, men er ikke nødvendig å lese for å bruke rammeverket. En lengre forklaring kan du finne under docs/explanations.

Variabelvelgeren består bak lerretet av to deler. VariableSelector og VariableSelectorOption.

**VariableSelectorOption** kan enten settes opp via set_variables() eller direkte. Denne delen holder styr på alle alternativene du har opprettet og brukes.

**VariableSelector** bruker alle alternativene som er opprettet og har metoder for å koble moduler til spesifikke variabler.
