-- Testdata for the `kontaktinfo` table (INSERT statements only).
-- Contact details reported together with a submission. NULLs are intentional.
-- The table is created by schema_sqlite.sql / schema_postgres.sql; `id` is
-- omitted so new rows can be appended without renumbering.
--
-- Forms: RA-0187 (monthly, 2026-01 .. 2026-12) and RA-0745 (yearly, 2024 .. 2026).
-- Each form has 3 units that are present in every period.

-- RA-0187: one row per active submission
INSERT INTO kontaktinfo (iso_period, skjema, ident, refnr, kontaktperson, epost, telefon, bekreftet_kontaktinfo, kommentar_kontaktinfo, kommentar_krevende) VALUES
    ('2026-01', 'RA-0187', '12111111', '1043f5eb9897', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, NULL),
    ('2026-01', 'RA-0187', '12222222', '0e91287fe6da', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, NULL),
    ('2026-01', 'RA-0187', '12333333', '2ec970116695', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL),
    ('2026-02', 'RA-0187', '12111111', 'a554ba7db0a3', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, NULL),
    ('2026-02', 'RA-0187', '12222222', '36dc58f7b6fe', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, NULL),
    ('2026-02', 'RA-0187', '12333333', '03cfdcfc6266', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL),
    ('2026-03', 'RA-0187', '12111111', 'd328cae82b47', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', 'Ny kontaktperson fra neste periode', NULL),
    ('2026-03', 'RA-0187', '12222222', '0a6c332d175b', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, NULL),
    ('2026-03', 'RA-0187', '12333333', '4174bdce57ea', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL),
    ('2026-04', 'RA-0187', '12111111', '409a1ee4f8f4', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, NULL),
    ('2026-04', 'RA-0187', '12222222', '6a20b724261f', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, 'Krevende utfylling'),
    ('2026-04', 'RA-0187', '12333333', '1be886d1097c', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL),
    ('2026-05', 'RA-0187', '12111111', '49c6730dc4c7', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, NULL),
    ('2026-05', 'RA-0187', '12222222', '5fb8757b3aa9', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', 'Ny kontaktperson fra neste periode', NULL),
    ('2026-05', 'RA-0187', '12333333', '9152e8a6196c', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL),
    ('2026-06', 'RA-0187', '12111111', 'c90ef31c1068', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, NULL),
    ('2026-06', 'RA-0187', '12222222', '0b02d1338d76', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, NULL),
    ('2026-06', 'RA-0187', '12333333', '39660976c36b', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL),
    ('2026-07', 'RA-0187', '12111111', '70d4db228838', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, NULL),
    ('2026-07', 'RA-0187', '12222222', 'cfe7d39638d5', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, NULL),
    ('2026-07', 'RA-0187', '12333333', '1d28dfe58f8d', 'NILS NORDAVIND', NULL, '41414141', '1', 'Ny kontaktperson fra neste periode', NULL),
    ('2026-08', 'RA-0187', '12111111', '316cdec82aad', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, 'Krevende utfylling'),
    ('2026-08', 'RA-0187', '12222222', '6e10fae97daf', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, NULL),
    ('2026-08', 'RA-0187', '12333333', 'bb5a1a0bf36e', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL),
    ('2026-09', 'RA-0187', '12111111', 'dff5e81c27f1', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, NULL),
    ('2026-09', 'RA-0187', '12222222', '5b866aff7218', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, NULL),
    ('2026-09', 'RA-0187', '12333333', 'b746cb5821bf', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL),
    ('2026-10', 'RA-0187', '12111111', '2d2080daed1a', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', 'Ny kontaktperson fra neste periode', NULL),
    ('2026-10', 'RA-0187', '12222222', '2dc0d6e06f76', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, NULL),
    ('2026-10', 'RA-0187', '12333333', 'e2f145547d1d', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL),
    ('2026-11', 'RA-0187', '12111111', '4cac6748f62d', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, NULL),
    ('2026-11', 'RA-0187', '12222222', 'fd2205a4af52', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', NULL, NULL),
    ('2026-11', 'RA-0187', '12333333', '46335ad9d19d', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, 'Krevende utfylling'),
    ('2026-12', 'RA-0187', '12111111', '98e53e3b80b0', 'NNAMREIB DRANOEL O', 'dranoel.nnamreib@ssb.no', '99889988', '1', NULL, NULL),
    ('2026-12', 'RA-0187', '12222222', '48f09da60c80', 'GRETE GRØNN', 'grete.gronn@example.no', '40404040', '1', 'Ny kontaktperson fra neste periode', NULL),
    ('2026-12', 'RA-0187', '12333333', 'f27caa26b082', 'NILS NORDAVIND', NULL, '41414141', '1', NULL, NULL);

-- RA-0745: one row per active submission
INSERT INTO kontaktinfo (iso_period, skjema, ident, refnr, kontaktperson, epost, telefon, bekreftet_kontaktinfo, kommentar_kontaktinfo, kommentar_krevende) VALUES
    ('2024', 'RA-0745', 'ATF2134660', 'f7d1ca75eddd', 'DOLLY DUCK', NULL, '12345678', '1', NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134661', 'bbd0615e340c', 'SOLVEIG SOL', 'solveig.sol@example.no', '90909090', '1', NULL, NULL),
    ('2024', 'RA-0745', 'ATF2134662', '9d11f653e144', 'VEGARD VESTRE', 'vegard.vestre@example.no', '91919191', '1', NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134660', '73e114ac6b8f', 'DOLLY DUCK', NULL, '12345678', '1', NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134661', '450b6127188b', 'SOLVEIG SOL', 'solveig.sol@example.no', '90909090', '1', NULL, NULL),
    ('2025', 'RA-0745', 'ATF2134662', '3ae6f6d1ab00', 'VEGARD VESTRE', 'vegard.vestre@example.no', '91919191', '1', 'Ny kontaktperson fra neste periode', NULL),
    ('2026', 'RA-0745', 'ATF2134660', 'f5ba8ae4cdd8', 'DOLLY DUCK', NULL, '12345678', '1', NULL, NULL),
    ('2026', 'RA-0745', 'ATF2134661', 'b250f49e78cb', 'SOLVEIG SOL', 'solveig.sol@example.no', '90909090', '1', NULL, 'Krevende utfylling'),
    ('2026', 'RA-0745', 'ATF2134662', '30897dbac7b6', 'VEGARD VESTRE', 'vegard.vestre@example.no', '91919191', '1', NULL, NULL);
