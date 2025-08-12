# Hva er en modul?

En modul er en gjenbrukbar komponent i ssb-dash-framework.

Grovt sett kan moduler deles inn i mer ferdige og 'fullverdige' moduler eller byggeblokker som krever mer tilpasning.

De har noen fellestrekk:
- **En spesifikk oppgave**: En modul kan for eksempel være ansvarlig for å vise en tabell, en annen for å presentere et diagram, og en tredje for å la brukeren se et PDF-skjema.
- **Selvstendig**: Hver modul inneholder logikken og brukergrensesnittet den trenger for sin oppgave. Dette gjør koden mer organisert.
- **Gjenbrukbar**: Noen moduler kan være generelle nok til å brukes flere steder i applikasjonen, eller til og med i andre applikasjoner.

Vanligvis inkluderes modulene enten som en fane/tab eller et vindu som inneholder modulen sitt grensesnitt og funksjonalitet. Modulene snakker ikke direkte med hverandre men kommuniserer via variabelvelgeren.

Årsaken til dette er at vi ikke ønsker at moduler skal ha direkte avhengigheter til hverandre, så det er enklere å plukke ut kun de bitene av rammeverket som du er interessert i.

```
🔎 Hva er faner/tabs og vinduer?

En fane/tab er en fane som dukker opp ved toppen i applikasjonen din.

Et vindu er en boks som legger seg "oppå" resten av applikasjonen og kan åpnes ved å klikke på en knapp i venstre marg.

Mange moduler finnes både som et vindu eller som en tab/fane. For eksempel EditingTable finnes både som EditingTableTab og EditingTableWindow.
Det er samme modul, men inkludert i rammeverket på hver sin måte så du kan få det som du vil.
```

Du kan finne dokumentasjon for modulene enten her: https://statisticsnorway.github.io/ssb-dash-framework/ i koden under src/ssb_dash_framework eller ved å skrive `help(modul_du_vil_ha_dokumentasjon_for)`
