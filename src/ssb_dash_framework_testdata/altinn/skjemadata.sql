-- Testdata for the `skjemadata` table (INSERT statements only).
-- Long-format form answers. `feltsti` is the full path, `dybde` the path depth
-- and `indeks` the position within the innermost repeating group. Root level
-- fields have NULL dybde/indeks; group fields use dybde 3, nested groups dybde 5.
-- The table is created by schema_sqlite.sql / schema_postgres.sql; `id` is
-- omitted so new rows can be appended without renumbering.
--
-- Forms: RA-0187 (monthly, 2026-01 .. 2026-12) and RA-0745 (yearly, 2024 .. 2026).
-- Each form has 3 units that are present in every period.

-- RA-0187 / 12111111 / 2026-01 / refnr 6bac48976d75 (inactive submission)
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-01', 'RA-0187', '12111111', '6bac48976d75', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4000', NULL, NULL, NULL),
    ('2026-01', 'RA-0187', '12111111', '6bac48976d75', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6000', 'omsetning', NULL, NULL);

-- RA-0187 / 12111111 / 2026-01 / refnr 1043f5eb9897
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-01', 'RA-0187', '12111111', '1043f5eb9897', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4005', NULL, NULL, NULL),
    ('2026-01', 'RA-0187', '12111111', '1043f5eb9897', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6007', 'omsetning', NULL, NULL),
    ('2026-01', 'RA-0187', '12111111', '1043f5eb9897', '/antallAnsatte', 'antallAnsatte', '4', NULL, NULL, NULL),
    ('2026-01', 'RA-0187', '12111111', '1043f5eb9897', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-01 / refnr 0e91287fe6da
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-01', 'RA-0187', '12222222', '0e91287fe6da', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4010', NULL, NULL, NULL),
    ('2026-01', 'RA-0187', '12222222', '0e91287fe6da', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6014', 'omsetning', NULL, NULL),
    ('2026-01', 'RA-0187', '12222222', '0e91287fe6da', '/antallAnsatte', 'antallAnsatte', '5', NULL, NULL, NULL),
    ('2026-01', 'RA-0187', '12222222', '0e91287fe6da', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-01 / refnr 2ec970116695
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-01', 'RA-0187', '12333333', '2ec970116695', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4015', NULL, NULL, NULL),
    ('2026-01', 'RA-0187', '12333333', '2ec970116695', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6021', 'omsetning', NULL, NULL),
    ('2026-01', 'RA-0187', '12333333', '2ec970116695', '/antallAnsatte', 'antallAnsatte', '6', NULL, NULL, NULL),
    ('2026-01', 'RA-0187', '12333333', '2ec970116695', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-02 / refnr a554ba7db0a3
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-02', 'RA-0187', '12111111', 'a554ba7db0a3', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4020', NULL, NULL, NULL),
    ('2026-02', 'RA-0187', '12111111', 'a554ba7db0a3', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6028', 'omsetning', NULL, NULL),
    ('2026-02', 'RA-0187', '12111111', 'a554ba7db0a3', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-02', 'RA-0187', '12111111', 'a554ba7db0a3', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-02 / refnr 36dc58f7b6fe
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-02', 'RA-0187', '12222222', '36dc58f7b6fe', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4025', NULL, NULL, NULL),
    ('2026-02', 'RA-0187', '12222222', '36dc58f7b6fe', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6035', 'omsetning', NULL, NULL),
    ('2026-02', 'RA-0187', '12222222', '36dc58f7b6fe', '/antallAnsatte', 'antallAnsatte', '4', NULL, NULL, NULL),
    ('2026-02', 'RA-0187', '12222222', '36dc58f7b6fe', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-02 / refnr 03cfdcfc6266
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-02', 'RA-0187', '12333333', '03cfdcfc6266', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4030', NULL, NULL, NULL),
    ('2026-02', 'RA-0187', '12333333', '03cfdcfc6266', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6042', 'omsetning', NULL, NULL),
    ('2026-02', 'RA-0187', '12333333', '03cfdcfc6266', '/antallAnsatte', 'antallAnsatte', '5', NULL, NULL, NULL),
    ('2026-02', 'RA-0187', '12333333', '03cfdcfc6266', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-03 / refnr d328cae82b47
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-03', 'RA-0187', '12111111', 'd328cae82b47', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4035', NULL, NULL, NULL),
    ('2026-03', 'RA-0187', '12111111', 'd328cae82b47', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6049', 'omsetning', NULL, NULL),
    ('2026-03', 'RA-0187', '12111111', 'd328cae82b47', '/antallAnsatte', 'antallAnsatte', '6', NULL, NULL, NULL),
    ('2026-03', 'RA-0187', '12111111', 'd328cae82b47', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-03 / refnr 0a6c332d175b
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-03', 'RA-0187', '12222222', '0a6c332d175b', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4040', NULL, NULL, NULL),
    ('2026-03', 'RA-0187', '12222222', '0a6c332d175b', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6056', 'omsetning', NULL, NULL),
    ('2026-03', 'RA-0187', '12222222', '0a6c332d175b', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-03', 'RA-0187', '12222222', '0a6c332d175b', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-03 / refnr 4174bdce57ea
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-03', 'RA-0187', '12333333', '4174bdce57ea', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4000', NULL, NULL, NULL),
    ('2026-03', 'RA-0187', '12333333', '4174bdce57ea', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6000', 'omsetning', NULL, NULL),
    ('2026-03', 'RA-0187', '12333333', '4174bdce57ea', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-03', 'RA-0187', '12333333', '4174bdce57ea', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-04 / refnr 409a1ee4f8f4
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-04', 'RA-0187', '12111111', '409a1ee4f8f4', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4005', NULL, NULL, NULL),
    ('2026-04', 'RA-0187', '12111111', '409a1ee4f8f4', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6007', 'omsetning', NULL, NULL),
    ('2026-04', 'RA-0187', '12111111', '409a1ee4f8f4', '/antallAnsatte', 'antallAnsatte', '4', NULL, NULL, NULL),
    ('2026-04', 'RA-0187', '12111111', '409a1ee4f8f4', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-04 / refnr 6a20b724261f
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-04', 'RA-0187', '12222222', '6a20b724261f', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4010', NULL, NULL, NULL),
    ('2026-04', 'RA-0187', '12222222', '6a20b724261f', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6014', 'omsetning', NULL, NULL),
    ('2026-04', 'RA-0187', '12222222', '6a20b724261f', '/antallAnsatte', 'antallAnsatte', '5', NULL, NULL, NULL),
    ('2026-04', 'RA-0187', '12222222', '6a20b724261f', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-04 / refnr 1be886d1097c
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-04', 'RA-0187', '12333333', '1be886d1097c', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4015', NULL, NULL, NULL),
    ('2026-04', 'RA-0187', '12333333', '1be886d1097c', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6021', 'omsetning', NULL, NULL),
    ('2026-04', 'RA-0187', '12333333', '1be886d1097c', '/antallAnsatte', 'antallAnsatte', '6', NULL, NULL, NULL),
    ('2026-04', 'RA-0187', '12333333', '1be886d1097c', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-05 / refnr 49c6730dc4c7
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-05', 'RA-0187', '12111111', '49c6730dc4c7', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4020', NULL, NULL, NULL),
    ('2026-05', 'RA-0187', '12111111', '49c6730dc4c7', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6028', 'omsetning', NULL, NULL),
    ('2026-05', 'RA-0187', '12111111', '49c6730dc4c7', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-05', 'RA-0187', '12111111', '49c6730dc4c7', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-05 / refnr 5fb8757b3aa9
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-05', 'RA-0187', '12222222', '5fb8757b3aa9', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4025', NULL, NULL, NULL),
    ('2026-05', 'RA-0187', '12222222', '5fb8757b3aa9', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6035', 'omsetning', NULL, NULL),
    ('2026-05', 'RA-0187', '12222222', '5fb8757b3aa9', '/antallAnsatte', 'antallAnsatte', '4', NULL, NULL, NULL),
    ('2026-05', 'RA-0187', '12222222', '5fb8757b3aa9', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-05 / refnr 9152e8a6196c
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-05', 'RA-0187', '12333333', '9152e8a6196c', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4030', NULL, NULL, NULL),
    ('2026-05', 'RA-0187', '12333333', '9152e8a6196c', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6042', 'omsetning', NULL, NULL),
    ('2026-05', 'RA-0187', '12333333', '9152e8a6196c', '/antallAnsatte', 'antallAnsatte', '5', NULL, NULL, NULL),
    ('2026-05', 'RA-0187', '12333333', '9152e8a6196c', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-06 / refnr c90ef31c1068
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-06', 'RA-0187', '12111111', 'c90ef31c1068', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4035', NULL, NULL, NULL),
    ('2026-06', 'RA-0187', '12111111', 'c90ef31c1068', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6049', 'omsetning', NULL, NULL),
    ('2026-06', 'RA-0187', '12111111', 'c90ef31c1068', '/antallAnsatte', 'antallAnsatte', '6', NULL, NULL, NULL),
    ('2026-06', 'RA-0187', '12111111', 'c90ef31c1068', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-06 / refnr 0b02d1338d76
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-06', 'RA-0187', '12222222', '0b02d1338d76', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4040', NULL, NULL, NULL),
    ('2026-06', 'RA-0187', '12222222', '0b02d1338d76', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6056', 'omsetning', NULL, NULL),
    ('2026-06', 'RA-0187', '12222222', '0b02d1338d76', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-06', 'RA-0187', '12222222', '0b02d1338d76', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-06 / refnr 39660976c36b
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-06', 'RA-0187', '12333333', '39660976c36b', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4000', NULL, NULL, NULL),
    ('2026-06', 'RA-0187', '12333333', '39660976c36b', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6000', 'omsetning', NULL, NULL),
    ('2026-06', 'RA-0187', '12333333', '39660976c36b', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-06', 'RA-0187', '12333333', '39660976c36b', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-07 / refnr 70d4db228838
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-07', 'RA-0187', '12111111', '70d4db228838', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4005', NULL, NULL, NULL),
    ('2026-07', 'RA-0187', '12111111', '70d4db228838', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6007', 'omsetning', NULL, NULL),
    ('2026-07', 'RA-0187', '12111111', '70d4db228838', '/antallAnsatte', 'antallAnsatte', '4', NULL, NULL, NULL),
    ('2026-07', 'RA-0187', '12111111', '70d4db228838', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-07 / refnr cfe7d39638d5
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-07', 'RA-0187', '12222222', 'cfe7d39638d5', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4010', NULL, NULL, NULL),
    ('2026-07', 'RA-0187', '12222222', 'cfe7d39638d5', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6014', 'omsetning', NULL, NULL),
    ('2026-07', 'RA-0187', '12222222', 'cfe7d39638d5', '/antallAnsatte', 'antallAnsatte', '5', NULL, NULL, NULL),
    ('2026-07', 'RA-0187', '12222222', 'cfe7d39638d5', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-07 / refnr 1d28dfe58f8d
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-07', 'RA-0187', '12333333', '1d28dfe58f8d', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4015', NULL, NULL, NULL),
    ('2026-07', 'RA-0187', '12333333', '1d28dfe58f8d', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6021', 'omsetning', NULL, NULL),
    ('2026-07', 'RA-0187', '12333333', '1d28dfe58f8d', '/antallAnsatte', 'antallAnsatte', '6', NULL, NULL, NULL),
    ('2026-07', 'RA-0187', '12333333', '1d28dfe58f8d', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-08 / refnr 316cdec82aad
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-08', 'RA-0187', '12111111', '316cdec82aad', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4020', NULL, NULL, NULL),
    ('2026-08', 'RA-0187', '12111111', '316cdec82aad', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6028', 'omsetning', NULL, NULL),
    ('2026-08', 'RA-0187', '12111111', '316cdec82aad', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-08', 'RA-0187', '12111111', '316cdec82aad', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-08 / refnr 6e10fae97daf
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-08', 'RA-0187', '12222222', '6e10fae97daf', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4025', NULL, NULL, NULL),
    ('2026-08', 'RA-0187', '12222222', '6e10fae97daf', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6035', 'omsetning', NULL, NULL),
    ('2026-08', 'RA-0187', '12222222', '6e10fae97daf', '/antallAnsatte', 'antallAnsatte', '4', NULL, NULL, NULL),
    ('2026-08', 'RA-0187', '12222222', '6e10fae97daf', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-08 / refnr bb5a1a0bf36e
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-08', 'RA-0187', '12333333', 'bb5a1a0bf36e', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4030', NULL, NULL, NULL),
    ('2026-08', 'RA-0187', '12333333', 'bb5a1a0bf36e', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6042', 'omsetning', NULL, NULL),
    ('2026-08', 'RA-0187', '12333333', 'bb5a1a0bf36e', '/antallAnsatte', 'antallAnsatte', '5', NULL, NULL, NULL),
    ('2026-08', 'RA-0187', '12333333', 'bb5a1a0bf36e', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-09 / refnr dff5e81c27f1
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-09', 'RA-0187', '12111111', 'dff5e81c27f1', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4035', NULL, NULL, NULL),
    ('2026-09', 'RA-0187', '12111111', 'dff5e81c27f1', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6049', 'omsetning', NULL, NULL),
    ('2026-09', 'RA-0187', '12111111', 'dff5e81c27f1', '/antallAnsatte', 'antallAnsatte', '6', NULL, NULL, NULL),
    ('2026-09', 'RA-0187', '12111111', 'dff5e81c27f1', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-09 / refnr 5b866aff7218
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-09', 'RA-0187', '12222222', '5b866aff7218', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4040', NULL, NULL, NULL),
    ('2026-09', 'RA-0187', '12222222', '5b866aff7218', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6056', 'omsetning', NULL, NULL),
    ('2026-09', 'RA-0187', '12222222', '5b866aff7218', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-09', 'RA-0187', '12222222', '5b866aff7218', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-09 / refnr b746cb5821bf
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-09', 'RA-0187', '12333333', 'b746cb5821bf', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4000', NULL, NULL, NULL),
    ('2026-09', 'RA-0187', '12333333', 'b746cb5821bf', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6000', 'omsetning', NULL, NULL),
    ('2026-09', 'RA-0187', '12333333', 'b746cb5821bf', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-09', 'RA-0187', '12333333', 'b746cb5821bf', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-10 / refnr 2d2080daed1a
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-10', 'RA-0187', '12111111', '2d2080daed1a', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4005', NULL, NULL, NULL),
    ('2026-10', 'RA-0187', '12111111', '2d2080daed1a', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6007', 'omsetning', NULL, NULL),
    ('2026-10', 'RA-0187', '12111111', '2d2080daed1a', '/antallAnsatte', 'antallAnsatte', '4', NULL, NULL, NULL),
    ('2026-10', 'RA-0187', '12111111', '2d2080daed1a', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-10 / refnr 2dc0d6e06f76
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-10', 'RA-0187', '12222222', '2dc0d6e06f76', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4010', NULL, NULL, NULL),
    ('2026-10', 'RA-0187', '12222222', '2dc0d6e06f76', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6014', 'omsetning', NULL, NULL),
    ('2026-10', 'RA-0187', '12222222', '2dc0d6e06f76', '/antallAnsatte', 'antallAnsatte', '5', NULL, NULL, NULL),
    ('2026-10', 'RA-0187', '12222222', '2dc0d6e06f76', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-10 / refnr e2f145547d1d
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-10', 'RA-0187', '12333333', 'e2f145547d1d', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4015', NULL, NULL, NULL),
    ('2026-10', 'RA-0187', '12333333', 'e2f145547d1d', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6021', 'omsetning', NULL, NULL),
    ('2026-10', 'RA-0187', '12333333', 'e2f145547d1d', '/antallAnsatte', 'antallAnsatte', '6', NULL, NULL, NULL),
    ('2026-10', 'RA-0187', '12333333', 'e2f145547d1d', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-11 / refnr 4cac6748f62d
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-11', 'RA-0187', '12111111', '4cac6748f62d', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4020', NULL, NULL, NULL),
    ('2026-11', 'RA-0187', '12111111', '4cac6748f62d', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6028', 'omsetning', NULL, NULL),
    ('2026-11', 'RA-0187', '12111111', '4cac6748f62d', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-11', 'RA-0187', '12111111', '4cac6748f62d', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-11 / refnr fd2205a4af52
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-11', 'RA-0187', '12222222', 'fd2205a4af52', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4025', NULL, NULL, NULL),
    ('2026-11', 'RA-0187', '12222222', 'fd2205a4af52', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6035', 'omsetning', NULL, NULL),
    ('2026-11', 'RA-0187', '12222222', 'fd2205a4af52', '/antallAnsatte', 'antallAnsatte', '4', NULL, NULL, NULL),
    ('2026-11', 'RA-0187', '12222222', 'fd2205a4af52', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-11 / refnr 46335ad9d19d
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-11', 'RA-0187', '12333333', '46335ad9d19d', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4030', NULL, NULL, NULL),
    ('2026-11', 'RA-0187', '12333333', '46335ad9d19d', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6042', 'omsetning', NULL, NULL),
    ('2026-11', 'RA-0187', '12333333', '46335ad9d19d', '/antallAnsatte', 'antallAnsatte', '5', NULL, NULL, NULL),
    ('2026-11', 'RA-0187', '12333333', '46335ad9d19d', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12111111 / 2026-12 / refnr 98e53e3b80b0
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-12', 'RA-0187', '12111111', '98e53e3b80b0', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4035', NULL, NULL, NULL),
    ('2026-12', 'RA-0187', '12111111', '98e53e3b80b0', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6049', 'omsetning', NULL, NULL),
    ('2026-12', 'RA-0187', '12111111', '98e53e3b80b0', '/antallAnsatte', 'antallAnsatte', '6', NULL, NULL, NULL),
    ('2026-12', 'RA-0187', '12111111', '98e53e3b80b0', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12222222 / 2026-12 / refnr 48f09da60c80
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-12', 'RA-0187', '12222222', '48f09da60c80', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4040', NULL, NULL, NULL),
    ('2026-12', 'RA-0187', '12222222', '48f09da60c80', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6056', 'omsetning', NULL, NULL),
    ('2026-12', 'RA-0187', '12222222', '48f09da60c80', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-12', 'RA-0187', '12222222', '48f09da60c80', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0187 / 12333333 / 2026-12 / refnr f27caa26b082
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026-12', 'RA-0187', '12333333', 'f27caa26b082', '/omsForrigePerPrefill', 'omsForrigePerPrefill', '4000', NULL, NULL, NULL),
    ('2026-12', 'RA-0187', '12333333', 'f27caa26b082', '/omsVirksomhetPerioden', 'omsVirksomhetPerioden', '6000', 'omsetning', NULL, NULL),
    ('2026-12', 'RA-0187', '12333333', 'f27caa26b082', '/antallAnsatte', 'antallAnsatte', '3', NULL, NULL, NULL),
    ('2026-12', 'RA-0187', '12333333', 'f27caa26b082', '/kommentarSkjema', 'kommentarSkjema', NULL, NULL, NULL, NULL);

-- RA-0745 / ATF2134660 / 2024 / refnr f7d1ca75eddd
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/prefillAreal', 'prefillAreal', '61', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/prefillVekstNavn', 'prefillVekstNavn', 'Fulldyrka eng', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/prefillVekstNummer', 'prefillVekstNummer', '2', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngArbJaNei', 'NyEngArbJaNei', '1', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngArbAreal', 'NyEngArbAreal', '51', 'areal', NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUts', 'NyEngSpredUts', '00,09', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjods', 'NyEngHusdyrGjods', '070,080', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/EngKommentar', 'EngKommentar', 'Kommentar for 2024', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/EtaEngHusdyrGjodsAreal', 'EtaEngHusdyrGjodsAreal', NULL, NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUtsGroup/0/NyEngSpredUtsID', 'NyEngSpredUtsID', '00', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUtsGroup/0/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Bredspreder for bløtgjødsel med tankvogn', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUtsGroup/0/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '31', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUtsGroup/9/NyEngSpredUtsID', 'NyEngSpredUtsID', '09', NULL, 3, 9),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUtsGroup/9/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Gjødselvogn med spredevalser for fastgjødsel', NULL, 3, 9),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUtsGroup/9/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '101', NULL, 3, 9),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUtsGroup/11/NyEngSpredUtsID', 'NyEngSpredUtsID', 'TOTAL_ROW', NULL, 3, 11),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUtsGroup/11/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Husdyrgjødsel spredd totalt', NULL, 3, 11),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngSpredUtsGroup/11/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '132', NULL, 3, 11),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '010', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'Fullgjødsel 8-5-19 mikro', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngMineralGjodsGroup/0/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '110', NULL, 3, 10),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'SULFAN 24-0-0', NULL, 3, 10),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngMineralGjodsGroup/10/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '1', NULL, 3, 10),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsID', 'NyEngHusdyrGjodsID', '070', NULL, 3, 6),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsNavn', 'NyEngHusdyrGjodsNavn', 'Bløtgjødsel storfe', NULL, 3, 6),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrAntallGjods', 'NyEngHusdyrAntallGjods', '3', NULL, 3, 6),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '0', NULL, 5, 0),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '34', NULL, 5, 0),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '3334', NULL, 5, 0),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '1', NULL, 5, 1),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '33', NULL, 5, 1),
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '321', NULL, 5, 1);

-- RA-0745 / ATF2134661 / 2024 / refnr bbd0615e340c
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/prefillAreal', 'prefillAreal', '62', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/prefillVekstNavn', 'prefillVekstNavn', 'Fulldyrka eng', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/prefillVekstNummer', 'prefillVekstNummer', '2', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngArbJaNei', 'NyEngArbJaNei', '1', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngArbAreal', 'NyEngArbAreal', '52', 'areal', NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUts', 'NyEngSpredUts', '00,09', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjods', 'NyEngHusdyrGjods', '070,080', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/EngKommentar', 'EngKommentar', 'Kommentar for 2024', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/EtaEngHusdyrGjodsAreal', 'EtaEngHusdyrGjodsAreal', NULL, NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUtsGroup/0/NyEngSpredUtsID', 'NyEngSpredUtsID', '00', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUtsGroup/0/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Bredspreder for bløtgjødsel med tankvogn', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUtsGroup/0/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '32', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUtsGroup/9/NyEngSpredUtsID', 'NyEngSpredUtsID', '09', NULL, 3, 9),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUtsGroup/9/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Gjødselvogn med spredevalser for fastgjødsel', NULL, 3, 9),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUtsGroup/9/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '102', NULL, 3, 9),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUtsGroup/11/NyEngSpredUtsID', 'NyEngSpredUtsID', 'TOTAL_ROW', NULL, 3, 11),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUtsGroup/11/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Husdyrgjødsel spredd totalt', NULL, 3, 11),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngSpredUtsGroup/11/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '134', NULL, 3, 11),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '010', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'Fullgjødsel 8-5-19 mikro', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngMineralGjodsGroup/0/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '110', NULL, 3, 10),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'SULFAN 24-0-0', NULL, 3, 10),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngMineralGjodsGroup/10/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '2', NULL, 3, 10),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsID', 'NyEngHusdyrGjodsID', '070', NULL, 3, 6),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsNavn', 'NyEngHusdyrGjodsNavn', 'Bløtgjødsel storfe', NULL, 3, 6),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrAntallGjods', 'NyEngHusdyrAntallGjods', '4', NULL, 3, 6),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '0', NULL, 5, 0),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '35', NULL, 5, 0),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '3335', NULL, 5, 0),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '1', NULL, 5, 1),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '34', NULL, 5, 1),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '322', NULL, 5, 1);

-- RA-0745 / ATF2134662 / 2024 / refnr 9d11f653e144
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/prefillAreal', 'prefillAreal', '63', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/prefillVekstNavn', 'prefillVekstNavn', 'Fulldyrka eng', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/prefillVekstNummer', 'prefillVekstNummer', '2', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngArbJaNei', 'NyEngArbJaNei', '1', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngArbAreal', 'NyEngArbAreal', '53', 'areal', NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUts', 'NyEngSpredUts', '00,09', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjods', 'NyEngHusdyrGjods', '070,080', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/EngKommentar', 'EngKommentar', 'Kommentar for 2024', NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/EtaEngHusdyrGjodsAreal', 'EtaEngHusdyrGjodsAreal', NULL, NULL, NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUtsGroup/0/NyEngSpredUtsID', 'NyEngSpredUtsID', '00', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUtsGroup/0/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Bredspreder for bløtgjødsel med tankvogn', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUtsGroup/0/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '33', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUtsGroup/9/NyEngSpredUtsID', 'NyEngSpredUtsID', '09', NULL, 3, 9),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUtsGroup/9/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Gjødselvogn med spredevalser for fastgjødsel', NULL, 3, 9),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUtsGroup/9/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '103', NULL, 3, 9),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUtsGroup/11/NyEngSpredUtsID', 'NyEngSpredUtsID', 'TOTAL_ROW', NULL, 3, 11),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUtsGroup/11/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Husdyrgjødsel spredd totalt', NULL, 3, 11),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngSpredUtsGroup/11/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '136', NULL, 3, 11),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '010', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'Fullgjødsel 8-5-19 mikro', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngMineralGjodsGroup/0/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 0),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '110', NULL, 3, 10),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'SULFAN 24-0-0', NULL, 3, 10),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngMineralGjodsGroup/10/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '3', NULL, 3, 10),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsID', 'NyEngHusdyrGjodsID', '070', NULL, 3, 6),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsNavn', 'NyEngHusdyrGjodsNavn', 'Bløtgjødsel storfe', NULL, 3, 6),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrAntallGjods', 'NyEngHusdyrAntallGjods', '5', NULL, 3, 6),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '0', NULL, 5, 0),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '36', NULL, 5, 0),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '3336', NULL, 5, 0),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '1', NULL, 5, 1),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '35', NULL, 5, 1),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '323', NULL, 5, 1);

-- RA-0745 / ATF2134660 / 2025 / refnr 73e114ac6b8f
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/prefillAreal', 'prefillAreal', '64', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/prefillVekstNavn', 'prefillVekstNavn', 'Fulldyrka eng', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/prefillVekstNummer', 'prefillVekstNummer', '2', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngArbJaNei', 'NyEngArbJaNei', '1', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngArbAreal', 'NyEngArbAreal', '54', 'areal', NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUts', 'NyEngSpredUts', '00,09', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjods', 'NyEngHusdyrGjods', '070,080', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/EngKommentar', 'EngKommentar', 'Kommentar for 2025', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/EtaEngHusdyrGjodsAreal', 'EtaEngHusdyrGjodsAreal', NULL, NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUtsGroup/0/NyEngSpredUtsID', 'NyEngSpredUtsID', '00', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUtsGroup/0/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Bredspreder for bløtgjødsel med tankvogn', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUtsGroup/0/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '34', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUtsGroup/9/NyEngSpredUtsID', 'NyEngSpredUtsID', '09', NULL, 3, 9),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUtsGroup/9/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Gjødselvogn med spredevalser for fastgjødsel', NULL, 3, 9),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUtsGroup/9/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '104', NULL, 3, 9),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUtsGroup/11/NyEngSpredUtsID', 'NyEngSpredUtsID', 'TOTAL_ROW', NULL, 3, 11),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUtsGroup/11/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Husdyrgjødsel spredd totalt', NULL, 3, 11),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngSpredUtsGroup/11/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '138', NULL, 3, 11),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '010', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'Fullgjødsel 8-5-19 mikro', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngMineralGjodsGroup/0/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '110', NULL, 3, 10),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'SULFAN 24-0-0', NULL, 3, 10),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngMineralGjodsGroup/10/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '4', NULL, 3, 10),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsID', 'NyEngHusdyrGjodsID', '070', NULL, 3, 6),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsNavn', 'NyEngHusdyrGjodsNavn', 'Bløtgjødsel storfe', NULL, 3, 6),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrAntallGjods', 'NyEngHusdyrAntallGjods', '6', NULL, 3, 6),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '0', NULL, 5, 0),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '37', NULL, 5, 0),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '3337', NULL, 5, 0),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '1', NULL, 5, 1),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '36', NULL, 5, 1),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '324', NULL, 5, 1);

-- RA-0745 / ATF2134661 / 2025 / refnr 450b6127188b
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/prefillAreal', 'prefillAreal', '65', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/prefillVekstNavn', 'prefillVekstNavn', 'Fulldyrka eng', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/prefillVekstNummer', 'prefillVekstNummer', '2', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngArbJaNei', 'NyEngArbJaNei', '1', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngArbAreal', 'NyEngArbAreal', '55', 'areal', NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUts', 'NyEngSpredUts', '00,09', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjods', 'NyEngHusdyrGjods', '070,080', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/EngKommentar', 'EngKommentar', 'Kommentar for 2025', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/EtaEngHusdyrGjodsAreal', 'EtaEngHusdyrGjodsAreal', NULL, NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUtsGroup/0/NyEngSpredUtsID', 'NyEngSpredUtsID', '00', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUtsGroup/0/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Bredspreder for bløtgjødsel med tankvogn', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUtsGroup/0/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '35', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUtsGroup/9/NyEngSpredUtsID', 'NyEngSpredUtsID', '09', NULL, 3, 9),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUtsGroup/9/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Gjødselvogn med spredevalser for fastgjødsel', NULL, 3, 9),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUtsGroup/9/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '105', NULL, 3, 9),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUtsGroup/11/NyEngSpredUtsID', 'NyEngSpredUtsID', 'TOTAL_ROW', NULL, 3, 11),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUtsGroup/11/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Husdyrgjødsel spredd totalt', NULL, 3, 11),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngSpredUtsGroup/11/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '140', NULL, 3, 11),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '010', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'Fullgjødsel 8-5-19 mikro', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngMineralGjodsGroup/0/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '110', NULL, 3, 10),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'SULFAN 24-0-0', NULL, 3, 10),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngMineralGjodsGroup/10/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '5', NULL, 3, 10),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsID', 'NyEngHusdyrGjodsID', '070', NULL, 3, 6),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsNavn', 'NyEngHusdyrGjodsNavn', 'Bløtgjødsel storfe', NULL, 3, 6),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrAntallGjods', 'NyEngHusdyrAntallGjods', '7', NULL, 3, 6),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '0', NULL, 5, 0),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '38', NULL, 5, 0),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '3338', NULL, 5, 0),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '1', NULL, 5, 1),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '37', NULL, 5, 1),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '325', NULL, 5, 1);

-- RA-0745 / ATF2134662 / 2025 / refnr 3ae6f6d1ab00
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/prefillAreal', 'prefillAreal', '66', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/prefillVekstNavn', 'prefillVekstNavn', 'Fulldyrka eng', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/prefillVekstNummer', 'prefillVekstNummer', '2', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngArbJaNei', 'NyEngArbJaNei', '1', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngArbAreal', 'NyEngArbAreal', '56', 'areal', NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUts', 'NyEngSpredUts', '00,09', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjods', 'NyEngHusdyrGjods', '070,080', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/EngKommentar', 'EngKommentar', 'Kommentar for 2025', NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/EtaEngHusdyrGjodsAreal', 'EtaEngHusdyrGjodsAreal', NULL, NULL, NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUtsGroup/0/NyEngSpredUtsID', 'NyEngSpredUtsID', '00', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUtsGroup/0/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Bredspreder for bløtgjødsel med tankvogn', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUtsGroup/0/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '36', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUtsGroup/9/NyEngSpredUtsID', 'NyEngSpredUtsID', '09', NULL, 3, 9),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUtsGroup/9/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Gjødselvogn med spredevalser for fastgjødsel', NULL, 3, 9),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUtsGroup/9/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '106', NULL, 3, 9),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUtsGroup/11/NyEngSpredUtsID', 'NyEngSpredUtsID', 'TOTAL_ROW', NULL, 3, 11),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUtsGroup/11/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Husdyrgjødsel spredd totalt', NULL, 3, 11),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngSpredUtsGroup/11/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '142', NULL, 3, 11),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '010', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'Fullgjødsel 8-5-19 mikro', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngMineralGjodsGroup/0/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 0),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '110', NULL, 3, 10),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'SULFAN 24-0-0', NULL, 3, 10),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngMineralGjodsGroup/10/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '6', NULL, 3, 10),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsID', 'NyEngHusdyrGjodsID', '070', NULL, 3, 6),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsNavn', 'NyEngHusdyrGjodsNavn', 'Bløtgjødsel storfe', NULL, 3, 6),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrAntallGjods', 'NyEngHusdyrAntallGjods', '8', NULL, 3, 6),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '0', NULL, 5, 0),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '39', NULL, 5, 0),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '3339', NULL, 5, 0),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '1', NULL, 5, 1),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '38', NULL, 5, 1),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '326', NULL, 5, 1);

-- RA-0745 / ATF2134660 / 2026 / refnr f5ba8ae4cdd8
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/prefillAreal', 'prefillAreal', '67', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/prefillVekstNavn', 'prefillVekstNavn', 'Fulldyrka eng', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/prefillVekstNummer', 'prefillVekstNummer', '2', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngArbJaNei', 'NyEngArbJaNei', '1', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngArbAreal', 'NyEngArbAreal', '57', 'areal', NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUts', 'NyEngSpredUts', '00,09', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjods', 'NyEngHusdyrGjods', '070,080', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/EngKommentar', 'EngKommentar', 'Kommentar for 2026', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/EtaEngHusdyrGjodsAreal', 'EtaEngHusdyrGjodsAreal', NULL, NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUtsGroup/0/NyEngSpredUtsID', 'NyEngSpredUtsID', '00', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUtsGroup/0/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Bredspreder for bløtgjødsel med tankvogn', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUtsGroup/0/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '37', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUtsGroup/9/NyEngSpredUtsID', 'NyEngSpredUtsID', '09', NULL, 3, 9),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUtsGroup/9/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Gjødselvogn med spredevalser for fastgjødsel', NULL, 3, 9),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUtsGroup/9/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '107', NULL, 3, 9),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUtsGroup/11/NyEngSpredUtsID', 'NyEngSpredUtsID', 'TOTAL_ROW', NULL, 3, 11),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUtsGroup/11/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Husdyrgjødsel spredd totalt', NULL, 3, 11),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngSpredUtsGroup/11/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '144', NULL, 3, 11),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '010', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'Fullgjødsel 8-5-19 mikro', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngMineralGjodsGroup/0/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '110', NULL, 3, 10),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'SULFAN 24-0-0', NULL, 3, 10),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngMineralGjodsGroup/10/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '7', NULL, 3, 10),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsID', 'NyEngHusdyrGjodsID', '070', NULL, 3, 6),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsNavn', 'NyEngHusdyrGjodsNavn', 'Bløtgjødsel storfe', NULL, 3, 6),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrAntallGjods', 'NyEngHusdyrAntallGjods', '9', NULL, 3, 6),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '0', NULL, 5, 0),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '40', NULL, 5, 0),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '3340', NULL, 5, 0),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '1', NULL, 5, 1),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '39', NULL, 5, 1),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '327', NULL, 5, 1);

-- RA-0745 / ATF2134661 / 2026 / refnr b250f49e78cb
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/prefillAreal', 'prefillAreal', '68', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/prefillVekstNavn', 'prefillVekstNavn', 'Fulldyrka eng', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/prefillVekstNummer', 'prefillVekstNummer', '2', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngArbJaNei', 'NyEngArbJaNei', '1', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngArbAreal', 'NyEngArbAreal', '58', 'areal', NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUts', 'NyEngSpredUts', '00,09', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjods', 'NyEngHusdyrGjods', '070,080', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/EngKommentar', 'EngKommentar', 'Kommentar for 2026', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/EtaEngHusdyrGjodsAreal', 'EtaEngHusdyrGjodsAreal', NULL, NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUtsGroup/0/NyEngSpredUtsID', 'NyEngSpredUtsID', '00', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUtsGroup/0/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Bredspreder for bløtgjødsel med tankvogn', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUtsGroup/0/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '38', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUtsGroup/9/NyEngSpredUtsID', 'NyEngSpredUtsID', '09', NULL, 3, 9),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUtsGroup/9/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Gjødselvogn med spredevalser for fastgjødsel', NULL, 3, 9),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUtsGroup/9/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '108', NULL, 3, 9),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUtsGroup/11/NyEngSpredUtsID', 'NyEngSpredUtsID', 'TOTAL_ROW', NULL, 3, 11),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUtsGroup/11/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Husdyrgjødsel spredd totalt', NULL, 3, 11),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngSpredUtsGroup/11/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '146', NULL, 3, 11),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '010', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'Fullgjødsel 8-5-19 mikro', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngMineralGjodsGroup/0/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '110', NULL, 3, 10),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'SULFAN 24-0-0', NULL, 3, 10),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngMineralGjodsGroup/10/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '8', NULL, 3, 10),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsID', 'NyEngHusdyrGjodsID', '070', NULL, 3, 6),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsNavn', 'NyEngHusdyrGjodsNavn', 'Bløtgjødsel storfe', NULL, 3, 6),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrAntallGjods', 'NyEngHusdyrAntallGjods', '10', NULL, 3, 6),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '0', NULL, 5, 0),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '41', NULL, 5, 0),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '3341', NULL, 5, 0),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '1', NULL, 5, 1),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '40', NULL, 5, 1),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '328', NULL, 5, 1);

-- RA-0745 / ATF2134662 / 2026 / refnr 30897dbac7b6
INSERT INTO skjemadata (iso_period, skjema, ident, refnr, feltsti, feltnavn, verdi, alias, dybde, indeks) VALUES
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/prefillAreal', 'prefillAreal', '60', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/prefillVekstNavn', 'prefillVekstNavn', 'Fulldyrka eng', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/prefillVekstNummer', 'prefillVekstNummer', '2', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngArbJaNei', 'NyEngArbJaNei', '1', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngArbAreal', 'NyEngArbAreal', '50', 'areal', NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUts', 'NyEngSpredUts', '00,09', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjods', 'NyEngHusdyrGjods', '070,080', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/EngKommentar', 'EngKommentar', 'Kommentar for 2026', NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/EtaEngHusdyrGjodsAreal', 'EtaEngHusdyrGjodsAreal', NULL, NULL, NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUtsGroup/0/NyEngSpredUtsID', 'NyEngSpredUtsID', '00', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUtsGroup/0/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Bredspreder for bløtgjødsel med tankvogn', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUtsGroup/0/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '30', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUtsGroup/9/NyEngSpredUtsID', 'NyEngSpredUtsID', '09', NULL, 3, 9),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUtsGroup/9/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Gjødselvogn med spredevalser for fastgjødsel', NULL, 3, 9),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUtsGroup/9/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '100', NULL, 3, 9),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUtsGroup/11/NyEngSpredUtsID', 'NyEngSpredUtsID', 'TOTAL_ROW', NULL, 3, 11),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUtsGroup/11/NyEngSpredUtsNavn', 'NyEngSpredUtsNavn', 'Husdyrgjødsel spredd totalt', NULL, 3, 11),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngSpredUtsGroup/11/NyEngSpredUtsGjodsMengde', 'NyEngSpredUtsGjodsMengde', '130', NULL, 3, 11),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '010', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngMineralGjodsGroup/0/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'Fullgjødsel 8-5-19 mikro', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngMineralGjodsGroup/0/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 0),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsID', 'NyEngMineralGjodsID', '110', NULL, 3, 10),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngMineralGjodsGroup/10/NyEngMineralGjodsNavn', 'NyEngMineralGjodsNavn', 'SULFAN 24-0-0', NULL, 3, 10),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngMineralGjodsGroup/10/NyEngMineralAntallGjods', 'NyEngMineralAntallGjods', '0', NULL, 3, 10),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsID', 'NyEngHusdyrGjodsID', '070', NULL, 3, 6),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodsNavn', 'NyEngHusdyrGjodsNavn', 'Bløtgjødsel storfe', NULL, 3, 6),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrAntallGjods', 'NyEngHusdyrAntallGjods', '2', NULL, 3, 6),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '0', NULL, 5, 0),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '33', NULL, 5, 0),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/0/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '3333', NULL, 5, 0),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAarstid', 'NyEngHGjodslingAarstid', '1', NULL, 5, 1),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingAreal', 'NyEngHGjodslingAreal', '32', NULL, 5, 1),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', '/NyEngHusdyrGjodsGroup/6/NyEngHusdyrGjodslinger/1/NyEngHGjodslingMengde', 'NyEngHGjodslingMengde', '320', NULL, 5, 1);
