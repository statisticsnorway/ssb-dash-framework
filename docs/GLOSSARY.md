# ssb-dash-framework

Shared language for building data editing apps from independent modules that review and correct statistical data.

## Language

### App coordination

**Variable selector**:
The shared panel of app-wide states (period, ident, grouping values, etc.) that is the only channel modules use to communicate.
_Avoid_: Variabelvelger (in English text), global state

**Period**:
The time unit value currently selected in the variable selector, such as a year, quarter or month.
_Avoid_: Year, aar, time variable

**Ident**:
The identifier of the statistical unit an observation describes.
_Avoid_: Orgnr, unit id

**Grouping variable**:
A categorical variable whose values split observations into groups for filtering or aggregation.
_Avoid_: Category, dimension, macro level

**Value variable**:
A numeric variable that is summed when observations are aggregated.
_Avoid_: Heatmap variable, metric, measure

**Codelist**:
The ordered set of valid codes, optionally with labels, for one grouping variable in a given period.
_Avoid_: Classification (when only the codes are meant), code table

**Klass codelist**:
A codelist published in SSB's classification system Klass; "klass" in conversation almost always means a codelist.
_Avoid_: Klass list, Klass classification (when only the codes are meant)

### Forms

**Submission**:
One delivery of a form by a unit for a period; a unit may deliver several submissions for the same form and period.
_Avoid_: Innsending, skjema (when one delivery is meant)

**Refnr**:
The identifier of one submission.
_Avoid_: Reference number, skjema-id

**Active submission**:
A submission marked as the one in use; when a unit has several, the most recently received one counts.
_Avoid_: Valid submission, current form

**Repeating group**:
A part of a form that a unit can fill in several times, each instance holding the same fields.
_Avoid_: Dynamic list, subtable, gruppe

### Data access

**Data model**:
The shape of the data a component expects, independent of how it is stored.
_Avoid_: Schema (when the storage layout is meant)

**Data handler**:
The swappable component that translates between a storage backend's data model and the data model a module expects.
_Avoid_: Connector, getter, fetcher
