-- Parquedit schema for the Altinn testdata. Load this before the data files.

CREATE TABLE IF NOT EXISTS enheter (
    iso_period VARCHAR,
    ident VARCHAR,
    skjema VARCHAR
);

CREATE TABLE IF NOT EXISTS enhetsinfo (
    iso_period VARCHAR,
    ident VARCHAR,
    variable VARCHAR,
    verdi VARCHAR
);

CREATE TABLE IF NOT EXISTS kontaktinfo (
    iso_period VARCHAR,
    skjema VARCHAR,
    ident VARCHAR,
    refnr VARCHAR,
    kontaktperson VARCHAR,
    epost VARCHAR,
    telefon VARCHAR,
    bekreftet_kontaktinfo VARCHAR,
    kommentar_kontaktinfo VARCHAR,
    kommentar_krevende VARCHAR
);

CREATE TABLE IF NOT EXISTS skjemamottak (
    iso_period VARCHAR,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    skjema VARCHAR,
    skjema_versjon VARCHAR,
    ident VARCHAR,
    refnr VARCHAR,
    kommentar VARCHAR,
    dato_mottatt TIMESTAMP,
    status VARCHAR,
    aktiv BOOLEAN
);

CREATE TABLE IF NOT EXISTS skjemadata (
    iso_period VARCHAR NOT NULL,
    skjema VARCHAR NOT NULL,
    ident VARCHAR NOT NULL,
    refnr VARCHAR NOT NULL,
    feltsti VARCHAR,
    feltnavn VARCHAR NOT NULL,
    verdi VARCHAR,
    alias VARCHAR,
    dybde INTEGER,
    indeks INTEGER
);
