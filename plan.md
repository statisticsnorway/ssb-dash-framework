# Implementation plan: HB methodology module for SSB Dash Framework

- The current implementation plan outlines the tasks and responsibilities for developing the HB methodology module within the SSB Dash Framework. It serves as a guide for both the AI-assisted development and user approval process. It uses `architecture_design_detailed` and the destilled `architecture.md` as the main source of implementation guidance. Keep them up to date with decitions made underway. 
Ensure that any deviations from the architecture are documented and approved through this plan. Se også `ssb-vaskify-design` for relevante design considerations.

- This plan is based on Implementation order list outlined in `Implementation order list.md`. It follows the structured sequence of tasks required to develop the HB methodology module, ensuring that each step is clearly defined, testable, and approved before proceeding to the next. The implementation history is managed by the developer. Each row is it's own clearly defined task with its associated details and status.
- Expect the developer to batch add tasks in to current tasks, and ask questions or seek clarifications whenever uncertainties arise.
- When developer pastes a step into the chat, you are supposed to act on that step. 
- Re-read the document often, as this document will be changed often.
- Do not fill in User fields; they are reserved for user input and approval only.
- ONLY WORK ON THE AFFECTED TASK

## Current tasks
| Task | Description/commit | AI- solution suggestion /or follow up | User apporval or follow up | Ai- follow up - if not approved - or new questions arrise | User apporval or follow up |
|---|---|---|---|---|---|




# History
## Define the HB public contract
| Task | Description/commit | AI- solution suggestion | User apporval or follow up | Ai- follow up - if not approved - or new questions arrise | User apporval or follow up |
|---|---|---|---|---|---|
| Define the common HB input schema | Add `unit_id`, canonical `period`, numeric `value`, optional `strata`, and configured selector context. |  |  |  |  |
| Add the HB data-handler interface | Add `HBDataHandlerMeta.get_hb_dataframe(...)`; keep it independent of Altinn queries and Vaskify calls. |  |  |  |  |
| Validate the common HB input schema | Add schema validation and reject duplicate `unit_id`/`period` combinations. |  |  |  |  |
| Test the HB input contract | Add unit tests for required columns, types, uniqueness, and clear errors. |  |  |  |  |
| Fiks HB kontrakten, den skal støtte rammeverkets TimeUnit  sine seks frekvenser |  | Utvid HB-kontraktens periodestøtte til rammeverkets seks kanoniske formater: YEAR (`YYYY`), HALF_YEAR (`YYYY-1`/`YYYY-2`), QUARTER (`YYYY-Q1`–`YYYY-Q4`), MONTH (`YYYY-MM`), WEEK (`YYYY-Www`) og DAY (`YYYY-MM-DD`). Valider periodeteksten mot konfigurert frekvens, og behold eksisterende krav til kolonner, typer og unikhet. | Godkjent: Implementer, Sjekk dette opp i mot alle stegene i `## Define the HB public contract` og sjekk at `architecture_design_detailed` og `architecture.md` er oppdatert med nye endringer og implikasjoner av det | approved - done - Oppdaterte planen med noen bugs som ble funnet. Dealer med det senere |  |