CREATE TABLE IF NOT EXISTS registrering (
    aar INTEGER,
    sekvensnummer INTEGER PRIMARY KEY,
    orgnr VARCHAR,
    dato_mottatt TIMESTAMP,
    kilde VARCHAR
);

CREATE TABLE IF NOT EXISTS v_registrering_versjon (
    orgnr VARCHAR,
    aar INTEGER,
    sekvensnummer INTEGER,
    versjon_nr INTEGER,
    antall_versjoner INTEGER,
    dato_mottatt TIMESTAMP
);

CREATE TABLE IF NOT EXISTS v_update_counts (
    sekvensnummer INTEGER PRIMARY KEY,
    antall_endringer INTEGER
);

CREATE TABLE IF NOT EXISTS tema_virksomhet (
    sekvensnummer INTEGER,
    felt VARCHAR,
    belop VARCHAR,
    char_verdi VARCHAR,
    data_type VARCHAR,
    PRIMARY KEY (sekvensnummer, felt)
);

CREATE TABLE IF NOT EXISTS tema_balanse (
    sekvensnummer INTEGER,
    felt VARCHAR,
    belop VARCHAR,
    PRIMARY KEY (sekvensnummer, felt)
);

CREATE TABLE IF NOT EXISTS tema_resultat (
    sekvensnummer INTEGER,
    felt VARCHAR,
    belop VARCHAR,
    PRIMARY KEY (sekvensnummer, felt)
);

CREATE TABLE IF NOT EXISTS tema_resultat_hist (
    hist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sekvensnummer INTEGER,
    felt VARCHAR,
    belop VARCHAR,
    endret_av VARCHAR,
    endret_dato TIMESTAMP,
    operation_type VARCHAR,
    process_type VARCHAR
);

CREATE TABLE IF NOT EXISTS tema_balanse_hist (
    hist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sekvensnummer INTEGER,
    felt VARCHAR,
    belop VARCHAR,
    endret_av VARCHAR,
    endret_dato TIMESTAMP,
    operation_type VARCHAR,
    process_type VARCHAR
);

CREATE TABLE IF NOT EXISTS kommentarfelt_test_2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    orgnr VARCHAR,
    nivaa VARCHAR,
    variabel VARCHAR,
    kommentar VARCHAR,
    versjon INTEGER,
    opprettet_av VARCHAR,
    opprettet TIMESTAMP,
    aktiv BOOLEAN
);

CREATE TABLE IF NOT EXISTS kontroller (
    aar INTEGER,
    tema VARCHAR,
    kontrollid VARCHAR,
    kategori VARCHAR,
    skildring VARCHAR,
    python_fn VARCHAR,
    sorteringsvariabel VARCHAR,
    sortering VARCHAR,
    sist_kjoert TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kontrollutslag (
    aar INTEGER,
    kontrollid VARCHAR,
    sekvensnummer INTEGER,
    orgnr VARCHAR,
    utslag VARCHAR,
    verdi VARCHAR,
    aktiv BOOLEAN,
    org_form VARCHAR,
    sn2025_1 VARCHAR,
    sn07_1 VARCHAR,
    sektor_2014 VARCHAR,
    undersektor_2014 VARCHAR
);

CREATE TABLE IF NOT EXISTS ssb_foretak (
    orgnr VARCHAR PRIMARY KEY,
    navn VARCHAR,
    org_form VARCHAR,
    sn2025_1 VARCHAR,
    sn07_1 VARCHAR,
    sf_type VARCHAR,
    f_kommunenr VARCHAR,
    statuskode VARCHAR,
    sysselsatte INTEGER,
    sektor_2014 VARCHAR,
    undersektor_2014 VARCHAR
);

CREATE TABLE IF NOT EXISTS enhet_opplysninger (
    sekvensnummer INTEGER,
    opplysning VARCHAR,
    PRIMARY KEY (sekvensnummer, opplysning)
);

CREATE TABLE IF NOT EXISTS mv_registrering_vtype (
    aar INTEGER,
    virksomhetstype VARCHAR,
    antall INTEGER,
    PRIMARY KEY (aar, virksomhetstype)
);

CREATE TABLE IF NOT EXISTS tema_omloepsmiddel (
    sekvensnummer INTEGER,
    rad_sti VARCHAR,
    felt VARCHAR,
    belop VARCHAR,
    char_verdi VARCHAR,
    PRIMARY KEY (sekvensnummer, rad_sti, felt)
);

-- Triggers to log edits and update counts dynamically in SQLite demo

CREATE TRIGGER IF NOT EXISTS tb_insert_trigger AFTER INSERT ON tema_balanse
WHEN current_setting('nspek_app.process_type') = 'editering'
BEGIN
    INSERT INTO tema_balanse_hist (
        sekvensnummer, felt, belop, endret_av, endret_dato, operation_type, process_type
    ) VALUES (
        NEW.sekvensnummer, NEW.felt, NEW.belop, current_setting('nspek_app.user_id'), now(), 'INSERT', current_setting('nspek_app.process_type')
    );

    INSERT INTO v_update_counts (sekvensnummer, antall_endringer)
    VALUES (NEW.sekvensnummer, 1)
    ON CONFLICT(sekvensnummer) DO UPDATE SET antall_endringer = antall_endringer + 1;
END;

CREATE TRIGGER IF NOT EXISTS tb_update_trigger AFTER UPDATE ON tema_balanse
WHEN current_setting('nspek_app.process_type') = 'editering'
BEGIN
    INSERT INTO tema_balanse_hist (
        sekvensnummer, felt, belop, endret_av, endret_dato, operation_type, process_type
    ) VALUES (
        NEW.sekvensnummer, NEW.felt, NEW.belop, current_setting('nspek_app.user_id'), now(), 'UPDATE', current_setting('nspek_app.process_type')
    );

    INSERT INTO v_update_counts (sekvensnummer, antall_endringer)
    VALUES (NEW.sekvensnummer, 1)
    ON CONFLICT(sekvensnummer) DO UPDATE SET antall_endringer = antall_endringer + 1;
END;

CREATE TRIGGER IF NOT EXISTS tr_insert_trigger AFTER INSERT ON tema_resultat
WHEN current_setting('nspek_app.process_type') = 'editering'
BEGIN
    INSERT INTO tema_resultat_hist (
        sekvensnummer, felt, belop, endret_av, endret_dato, operation_type, process_type
    ) VALUES (
        NEW.sekvensnummer, NEW.felt, NEW.belop, current_setting('nspek_app.user_id'), now(), 'INSERT', current_setting('nspek_app.process_type')
    );

    INSERT INTO v_update_counts (sekvensnummer, antall_endringer)
    VALUES (NEW.sekvensnummer, 1)
    ON CONFLICT(sekvensnummer) DO UPDATE SET antall_endringer = antall_endringer + 1;
END;

CREATE TRIGGER IF NOT EXISTS tr_update_trigger AFTER UPDATE ON tema_resultat
WHEN current_setting('nspek_app.process_type') = 'editering'
BEGIN
    INSERT INTO tema_resultat_hist (
        sekvensnummer, felt, belop, endret_av, endret_dato, operation_type, process_type
    ) VALUES (
        NEW.sekvensnummer, NEW.felt, NEW.belop, current_setting('nspek_app.user_id'), now(), 'UPDATE', current_setting('nspek_app.process_type')
    );

    INSERT INTO v_update_counts (sekvensnummer, antall_endringer)
    VALUES (NEW.sekvensnummer, 1)
    ON CONFLICT(sekvensnummer) DO UPDATE SET antall_endringer = antall_endringer + 1;
END;
