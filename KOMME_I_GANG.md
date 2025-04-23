# Komme i gang

Denne veiledning har som mål å hjelpe deg frem til et fungerende oppsett som du senere kan utvide.

I første avsnitt får du en veiledning til hvordan du setter opp rammeverket.
- Denne antar at du har dataene på en struktur og teknologi som passer rammeverket. Du kan finne informasjon om datastruktur og lagringsteknologi **ett eller annet sted (husk å fikse noe her)**

Du får også noen hint om hvor du kan finne informasjon om hvilke moduler som finnes.

Mer forklaring om hva som egentlig foregår, logikken bak det og hvordan det henger sammen forklares senere om du er interessert.
- Detaljerte forklaringer er å finne i [README] og [contributor guide].
- Dokumentasjon om rammeverkets moduler kan du finne her: https://statisticsnorway.github.io/ssb-dash-framework/

## Ordliste

Her finner du en kort forklaring av hva som menes med visse ord i veiledningen.

- App : Applikasjonen du setter opp
- Variabelvelger : Funksjonalitet som deler informasjon om valgte variabler mellom moduler
- Modul : Komponent i dashbordet
- Window : Et vindu som inneholder en modul og åpnes med en knapp i venstre marg
- Tab : En fane langs toppen i skjermbildet som inneholder en modul

## Sett opp rammeverket på 1, 2, 3

Nedenfor er det en kort veiledning for hvordan du setter opp rammeverket, så kan du fylle det med moduler etter du har fått bekreftet at selve rammeverket fungerer. For å se eksempler på ferdige apper kan du se på [demo-repoet vårt](https://github.com/statisticsnorway/demo-ssb-dash).

### 1. Sett opp rammeverkets byggeklosser

I tillegg til koden for app_setup, så må du også sette opp variabelvelgeren før du går videre.

Du må legge inn alle variabler du vil ha tilgjengelig. Se nederste linje i koden nedenfor for å se hvordan du legger til en variabel. Du må legge til variablene en av gangen, og du må legge inn alle som skal benyttes for å filtrere eller identifisere observasjoner i appen din. Dette kan være variabler som år, måned, orgnr, nace o.l.

```python
from ssb_dash_framework import app_setup
from ssb_dash_framework import VariableSelectorOption

port = 8070
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, domain, "darkly")

VariableSelectorOption("foretak")
```

### 2. Importer og start modulene du vil ha

Vær oppmerksom på at noen moduler krever mer tilpasninger enn andre. Hva som kreves kan du se i dokumentasjonen for de enkelte modulene.

Importen av moduler skal legges langs toppen av scriptet med de andre importene mens oppsett av modulene skal skje under oppsettet av variabelvelgeren.

Vi anbefaler sterkt å importere moduler fra ssb_dash_framework på måten som er vist nedenfor. Dette er bruken vi støtter og du vil oppleve færre problemer om du holder deg til den. Om du heller ønsker å importere på andre måter kan du gjøre dette, men det medfører økt sjanse for breaking changes.

```python
from ssb_dash_framework import PimemorizerTab

# Din kode fra tidligere steg #

min_pi_memorizer = PimemorizerTab()
```

### 3. Sett sammen delene og start opp applikasjonen

Nå er det på tide å "montere" applikasjonen din. Dette gjør du ved å lage 3 [lister](https://realpython.com/python-list/):
- window_list

    Denne skal inneholde alle vindu-modulene dine

- tab_list

    Denne skal inneholde alle tab-modulene dine.

- variable_list

    Her skal du liste opp hvilke variabler som skal eksistere i variabelvelgeren. Det er viktig at alle variabler du skal bruke er definert som beskrevet i steg 1,5

Deretter skal du kjøre main_layout funksjonen for å definere appen din, og starte appen.

```python
modal_list = [
]

tab_list = [
    min_pi_memorizer,
]

variable_list = [
    "foretak", # f.eks. organisasjonsnummer
]

app.layout = main_layout(modal_list, tab_list, variable_list)
if __name__ == "__main__":
    app.run(
        port=port,
        jupyter_server_url=domain,
        jupyter_mode="tab"
    )
```

> 💡 **Hvorfor if ```__name__ == "__main__":```?**
>
> if ```__name__ == __main__:``` betyr at det som er dekket av if-statementen ikke vil kjøres med mindre du kjører denne filen direkte. Det er for å hindre at du kommer borti å importere filen i et annet script og starter appen ved et uhell.


## Hvilke moduler finnes?

Den enkle måten å bruke moduler er å bruke de som er "pakket inn" som enten et vindu eller en tab. Du kan finne disse her:
- Tabs [dokumentasjon](https://statisticsnorway.github.io/ssb-dash-framework/ssb_dash_framework.tabs.html) ([direkte i koden](https://github.com/statisticsnorway/ssb-dash-framework/tree/main/src/ssb_dash_framework/tabs))
- Vindu [dokumentasjon](https://statisticsnorway.github.io/ssb-dash-framework/ssb_dash_framework.windows.html) ([direkte i koden](https://github.com/statisticsnorway/ssb-dash-framework/tree/main/src/ssb_dash_framework/windows))

Alle moduler som finnes i dashbordet kan du se i [modul-dokumentasjonen](https://statisticsnorway.github.io/ssb-dash-framework/ssb_dash_framework.modules.html) ([direkte i koden](https://github.com/statisticsnorway/ssb-dash-framework/tree/main/src/ssb_dash_framework/modules)). Vær oppmerksom på at å bruke disse direkte er for mer avanserte brukere.

## Mer detaljerte forklaringer

**Det er ikke nødvendig å lese eller forstå dette for å bruke rammeverket.**

I denne bolken er vi innom litt mer detaljer som er til hjelp for å forstå hva som foregår og rammeverket er lagt opp som det er.

For enda mer teknisk dokumentasjon, som for eksempel hvordan lage din egen modul, se på [contributor guide].

### Tanken som former rammeverket

Hele rammeverket er lagt opp til at man skal tilnærme seg dataene sine fra makro (oversikt, helhet) og bevege seg til mikro (enkeltobservasjon) ved behov. Du skal finne enheter å sjekke basert på overordnede oversikter, visualiseringer og automatiske sjekker/kontroller.

Andre mål i rammeverket er lav terskel for å ta det i bruk og fleksibilitet i måten det brukes. Disse er til tider motstridende, siden fleksibilitet krever flere muligheter, men flere muligheter øker brukerterskelen.

Hvilket hensyn som styrer mest vil variere mellom moduler. BoF modulen som lar deg få rask tilgang til opplysninger om bedrifter og foretak vil naturligvis være enklere å ta i bruk enn en modul med mer skreddersydde visualiseringer og metoder som må tilpasses ulike datakilder og behov.

Rammeverket er designet slik at om du har behov som ikke dekkes så kan det utvides. Enten om du vil gjøre mindre tilpasninger eller lage helt egne moduler.

Hvis du lager en egen modul og denne kan være nyttig for flere, er det ønskelig å legge den inn i rammeverket.
Disse mer avanserte bruksmåtene beskrives i CONTRIBUTING.md.

### Hva skjer egentlig når du setter opp en modul?

Når du starter opp en modul "instansierer" du en "class". Enkelt forklart betyr det at python setter opp et objekt som python vet at har visse egenskaper
- et eksempel på et annet objekt i python er pandas dataframe, som har kolonner, en index og data.
- Modul objektet har visse egenskaper, som for eksempel .layout() metoden som lager det synlige brukergrensesnittet (knapper, grafer, tekst, osv.) til modulen.

Dette gjør at modulen kan sette opp koblinger, interaksjoner og mer som den trenger for å fungeremed minimalt av input fra deg som bruker.

I tillegg er det slik at hver modul har en "base class" som brukes av ModuleTab og ModuleWindow for å gjøre modulen tilgjengelig som en tab eller et vindu. Dette oppsettet gjør at hvis du vil gjenbruke en modul uten å bruke noe annet fra rammeverket, så er det mulig å få til.

### Hvordan snakker egentlig modulene med hverandre? Variabelvelgeren!

Rammeverket baserer seg på at man plukker ut moduler man ønsker å bruke og at variabelvelgeren knytter disse sammen.

Variabelvelgeren er limet som holder applikasjonen sammen og gjør at de ulike komponentene kan dele informasjon. Den skal brukes av andre moduler for å koordinere visninger mellom moduler og gjøre at du kan endre f.eks. næringskoden i variabelvelgeren, og alle skjermbilder vil vise informasjon om enheter med den næringskoden.

Variabelvelgeren fungerer som et felles punkt for informasjon som skal deles mellom ulike moduler i appen. Hvis du for eksempel sjekker et skjermbilde hvor det vises en enhet som du vil se på i et annet skjermbilde, så kan du i noen moduler klikke på enheten for å få enheten sin id overført til variabelvelgeren. Variabelvelgeren vil da formidle at det er den enheten vi vil se på til de andre modulene i appen slik at alle viser den samme enheten. På samme måte, hvis du vet at det er én spesifikk enhet du skal se på kan du skrive den direkte inn i variabelvelgeren.

**VIKTIG!** Variabelvelgeren skal gi inputs til andre skjermbilder og fungere som et søkefelt, den skal __ikke__ brukes for å vise informasjon om enheten man er inne på.


<!-- github-only -->
[contributor guide]: https://github.com/statisticsnorway/ssb-dash-framework/blob/main/CONTRIBUTING.md
[README]: https://github.com/statisticsnorway/ssb-dash-framework/blob/main/README.md
