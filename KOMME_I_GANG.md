# Komme i gang

Denne veiledning har som mål å hjelpe deg frem til et fungerende oppsett som du senere kan utvide.

I første avsnitt får du en veiledning til hvordan du setter opp rammeverket.
- Denne antar at du har dataene på en struktur og teknologi som passer rammeverket. Du kan finne informasjon om datastruktur og lagringsteknologi (et sted? Her?)

Mer forklaring om hva som egentlig foregår, logikken bak det og hvordan det henger sammen forklares senere om du er interessert.
- Mer grundige tekniske forklaringer er å finne i [README] og [contributor guide].
- Dokumentasjon om rammeverkets moduler kan du finne her: https://statisticsnorway.github.io/ssb-sirius-dash/

## Ordliste

Her finner du en kort forklaring av hva som menes med visse ord i veiledningen.

- App : Applikasjonen du setter opp
- Modul : Komponent i dashbordet
- Modal : Et vindu som inneholder en modul og åpnes med en knapp i venstre marg
- Tab : En fane i skjermbildet under variabelvelgeren som inneholder en modul

## Sett opp rammeverket på 1, 2, 3

Bruker du jupyter trenger du dette

```
port = 8070
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, domain, "superhero")
```

### 1. Hent inn de nødvendige byggeklossene og opprett app-objektet

```
from ssb_dash_framework.setup.main_layout import main_layout
from ssb_dash_framework.setup.app_setup import app_setup

app = app_setup(port, service_prefix, domain, "superhero")
```

### 2. Importer og start modulene du vil ha

Obs! Noen moduler krever mer tilpasninger enn andre. Dette kan du se i dokumentasjonen for de enkelte modulene som er henvist til tidligere.

```
from ssb_dash_framework.tabs.pi_memorizer import PimemorizerTab

min_pi_memorizer = PimemorizerTab()
```

### 3. Sett sammen delene og start opp applikasjonen

```
modal_list = [
]

tab_list = [
    min_pi_memorizer,
]

variable_list = [
    "min_id_variabel", # f.eks. organisasjonsnummer
    "min grupperingsvariabel", # f.eks. næringskode
]

app.layout = main_layout(modal_list, tab_list, variable_list)
if __name__ == "__main__":
    app.run(
        port=port,
        jupyter_server_url=domain,
        jupyter_mode="tab"
    )
```

## Mer forklaring

### Tanken som former rammeverket

Hele rammeverket er lagt opp til at man skal tilnærme seg dataene sine fra makro (oversikt, helhet) og bevege seg til mikro (enkeltobservasjon) ved behov. Du skal finne enheter å sjekke basert på overordnede oversikter, visualiseringer og automatiske sjekker/kontroller.

Andre mål i rammeverket er lav terskel for å ta det i bruk og fleksibilitet i måten det brukes. Disse er til tider motstridende, siden fleksibilitet krever flere muligheter, men flere muligheter øker brukerterskelen.

Hvilket hensyn som styrer mest vil variere mellom moduler. BoF modulen som lar deg få rask tilgang til opplysninger om bedrifter og foretak vil naturligvis være enklere å ta i bruk enn en modul med mer skreddersydde visualiseringer og metoder.

Det er en tanke at det skal være lett å bygge ut rammeverket om du har behov som ikke dekkes. Enten om du vil gjøre mindre tilpasninger eller lage helt egne moduler. Hvis du lager en egen modul og denne kan være nyttig for flere, er det ønskelig å legge den inn i rammeverket.
- Måten du gjør dette beskrives i CONTRIBUTING.md

### Hva skjer egentlig når du setter opp en modul?

Når du starter opp en modul "instansierer" du en "class". Enkelt forklart betyr det at python setter opp et objekt (et eksempel på et annet objekt i python er pandas dataframe).
- Dette objektet har visse egenskaper, som for eksempel .layout() metoden som lager det synlige brukergrensesnittet (knapper, grafer, tekst, osv.) til modulen.

Dette gjør at modulen kan sette opp koblinger, interaksjoner og mer som den trenger med minimalt av input fra deg som bruker.

### Hvordan snakker egentlig modulene med hverandre? Variabelvelgeren!

Rammeverket baserer seg på at man plukker ut moduler man ønsker å bruke og at variabelvelgeren knytter disse sammen.

variabelvelgeren er limet som holder applikasjonen sammen og gjør at de ulike komponentene kan dele informasjon. Den skal brukes av andre moduler for å koordinere visninger mellom moduler og gjøre at du kan endre f.eks. næringskoden i variabelvelgeren, og alle skjermbilder vil vise informasjon om enheter med den næringskoden.

Variabelvelgeren fungerer som et felles punkt for informasjon som skal deles mellom ulike modaler og tabs i appen. Hvis du for eksempel sjekker et skjermbilde hvor det vises en enhet som du vil se på i et annet skjermbilde, så kan du i noen moduler klikke på enheten for å få enheten sin id overført til variabelvelgeren. Variabelvelgeren vil da formidle at det er den enheten vi vil se på til de andre modulene i appen slik at alle viser den samme enheten. På samme måte, hvis du vet at det er én spesifikk enhet du skal se på kan du skrive den direkte inn i variabelvelgeren.

VIKTIG. Variabelvelgeren skal gi inputs til andre skjermbilder og fungere som et søkefelt, den skal __ikke__ brukes for å vise informasjon om enheten man er inne på.


<!-- github-only -->
[contributor guide]: https://github.com/statisticsnorway/ssb-sirius-dash/blob/main/CONTRIBUTING.md
[README]: https://github.com/statisticsnorway/ssb-sirius-dash/blob/main/README.md
