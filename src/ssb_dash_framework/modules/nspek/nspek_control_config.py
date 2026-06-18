from collections import defaultdict
from typing import Dict, List, Optional

CONTROL_RULES = [

    # =========================
    # RESULTATREGNSKAP
    # =========================

    {
        "kontrollid": "kontroll_driftsinntekt",
        "tema": "Resultat",
        "kategori": "H",
        "skildring": "Driftsinntekt stemmer ikke",
        "lhs": "sumDriftsinntekt",
        "threshold": 1000,
        "terms": [
            ("3000", 1),
            ("3001", 1),
            ("3002", 1),
            ("3003", 1),
            ("3004", 1),
            ("3005", 1),
            ("3006", 1),
            ("3007", 1),
            ("3008", 1),
            ("3100", 1),
            ("3200", 1),
            ("3300", -1),
            ("3400", 1),
            ("3500", 1),
            ("3600", 1),
            ("3650", 1),
            ("3695", 1),
            ("3700", 1),
            ("3710", 1),
            ("3850", 1),
            ("3870", 1),
            ("3880", 1),
            ("3885", 1),
            ("3886", 1),
            ("3890", 1),
            ("3895", 1),
            ("3900", 1),
            ("3910", 1),
            ("3911", 1),
        ],
    },

    {
        "kontrollid": "kontroll_driftskostnad",
        "tema": "Resultat",
        "kategori": "H",
        "skildring": "Driftskostnad stemmer ikke",
        "lhs": "sumDriftskostnad",
        "threshold": 1000,
        "terms": [
            ("4001", 1),
            ("4002", 1),
            ("4003", 1),
            ("4004", 1),
            ("4005", 1),
            ("4007", 1),
            ("4008", 1),
            ("4295", 1),
            ("4500", 1),
            ("4995", -1),
            ("5000", 1),
            ("5300", 1),
            ("5400", 1),
            ("5420", 1),
            ("5600", 1),
            ("5900", 1),
            ("5950", 1),
            ("6000", 1),
            ("6001", 1),
            ("6002", 1),
            ("6004", 1),
            ("6050", 1),
            ("6051", 1),
            ("6052", 1),
            ("6053", 1),
            ("6054", 1),
            ("6100", 1),
            ("6110", 1),
            ("6120", 1),
            ("6130", 1),
            ("6140", 1),
            ("6200", 1),
            ("6300", 1),
            ("6340", 1),
            ("6350", 1),
            ("6395", 1),
            ("6400", 1),
            ("6440", 1),
            ("6500", 1),
            ("6600", 1),
            ("6695", 1),
            ("6700", 1),
            ("6750", 1),
            ("6751", 1),
            ("6752", 1),
            ("6995", 1),
            ("6998", -1),
            ("7000", 1),
            ("7020", 1),
            ("7040", 1),
            ("7080", 1),
            ("7099", -1),
            ("7155", 1),
            ("7165", 1),
            ("7295", 1),
            ("7330", 1),
            ("7350", 1),
            ("7370", 1),
            ("7400", 1),
            ("7420", 1),
            ("7440", 1),
            ("7490", 1),
            ("7500", 1),
            ("7501", 1),
            ("7502", 1),
            ("7503", 1),
            ("7565", 1),
            ("7600", 1),
            ("7650", 1),
            ("7651", 1),
            ("7700", 1),
            ("7701", 1),
            ("7830", 1),
            ("7860", 1),
            ("7880", 1),
            ("7885", 1),
            ("7886", 1),
            ("7890", 1),
            ("7897", 1),
            ("7910", 1),
            ("7911", 1),
            ("7912", 1),
            ("7913", 1),
        ],
    },

    {
        "kontrollid": "kontroll_finansinntekt",
        "tema": "Resultat",
        "kategori": "H",
        "skildring": "Finansinntekt stemmer ikke",
        "lhs": "sumFinansinntekt",
        "threshold": 1000,
        "terms": [
            ("8005", 1),
            ("8030", 1),
            ("8050", 1),
            ("8054", 1),
            ("8059", 1),
            ("8060", 1),
            ("8074", 1),
            ("8075", 1),
            ("8079", 1),
            ("8080", 1),
            ("8090", 1),
            ("8091", 1),
        ],
    },

    {
        "kontrollid": "kontroll_finanskostnad",
        "tema": "Resultat",
        "kategori": "H",
        "skildring": "Finanskostnad stemmer ikke",
        "lhs": "sumFinanskostnad",
        "threshold": 1000,
        "terms": [
            ("8100", 1),
            ("8105", 1),
            ("8115", 1),
            ("8120", 1),
            ("8130", 1),
            ("8150", 1),
            ("8154", 1),
            ("8159", 1),
            ("8160", 1),
            ("8174", 1),
            ("8175", 1),
            ("8179", 1),
        ],
    },

    {
        "kontrollid": "kontroll_skattekostnad",
        "tema": "Resultat",
        "kategori": "H",
        "skildring": "Skattekostnad stemmer ikke",
        "lhs": "sumSkattekostnad",
        "threshold": 1000,
        "terms": [
            ("8300", 1),
            ("8321", 1),
            ("8322", -1),
            ("8323", 1),
            ("8324", -1),
        ],
    },

    {
        "kontrollid": "kontroll_aarsresultat",
        "tema": "Resultat",
        "kategori": "H",
        "skildring": "Årsresultat stemmer ikke",
        "lhs": "aarsresultat",
        "threshold": 1000,
        "terms": [
            ("sumDriftsinntekt", 1),
            ("sumDriftskostnad", -1),
            ("sumFinansinntekt", 1),
            ("sumFinanskostnad", -1),
            ("sumSkattekostnad", -1),
        ],
    },

    # =========================
    # BALANSE
    # =========================

    {
        "kontrollid": "kontroll_anleggsmidler",
        "tema": "Balanse",
        "kategori": "H",
        "skildring": "Anleggsmidler stemmer ikke",
        "lhs": "sumBalanseverdiForAnleggsmiddel",
        "threshold": 1000,
        "terms": [
            ("1000", 1),
            ("1020", 1),
            ("1070", 1),
            ("1080", 1),
            ("1101", 1),
            ("1102", 1),
            ("1103", 1),
            ("1104", 1),
            ("1105", 1),
            ("1115", 1),
            ("1117", 1),
            ("1120", 1),
            ("1130", 1),
            ("1140", 1),
            ("1150", 1),
            ("1160", 1),
            ("1180", 1),
            ("1205", 1),
            ("1221", 1),
            ("1225", 1),
            ("1238", 1),
            ("1280", 1),
            ("1290", 1),
            ("1295", 1),
            ("1296", -1),
            ("1298", -1),
            ("1299", -1),
            ("1312", 1),
            ("1313", 1),
            ("1320", 1),
            ("1331", 1),
            ("1332", 1),
            ("1340", 1),
            ("1350", 1),
            ("1360", 1),
            ("1370", 1),
            ("1380", 1),
            ("1390", 1),
            ("1395", 1),
        ],
    },

    {
        "kontrollid": "kontroll_omloepsmidler",
        "tema": "Balanse",
        "kategori": "H",
        "skildring": "Omløpsmidler stemmer ikke",
        "lhs": "sumBalanseverdiForOmloepsmiddel",
        "threshold": 1000,
        "terms": [
            ("1400", 1),
            ("1401", 1),
            ("1470", 1),
            ("1490", 1),
            ("1500", 1),
            ("1501", 1),
            ("1530", 1),
            ("1560", 1),
            ("1565", 1),
            ("1570", 1),
            ("1780", 1),
            ("1800", 1),
            ("1810", 1),
            ("1830", 1),
            ("1840", 1),
            ("1880", 1),
            ("1895", 1),
            ("1900", 1),
            ("1920", 1),
            ("1950", 1),
        ],
    },

    {
        "kontrollid": "kontroll_eiendeler",
        "tema": "Balanse",
        "kategori": "H",
        "skildring": "Eiendeler stemmer ikke",
        "lhs": "sumBalanseverdiForEiendel",
        "threshold": 1000,
        "terms": [
            ("sumBalanseverdiForAnleggsmiddel", 1),
            ("sumBalanseverdiForOmloepsmiddel", 1),
        ],
    },

    {
        "kontrollid": "kontroll_egenkapital",
        "tema": "Balanse",
        "kategori": "H",
        "skildring": "Egenkapital stemmer ikke",
        "lhs": "sumEgenkapital",
        "threshold": 1000,
        "terms": [
            ("2000", 1),
            ("2010", -1),
            ("2015", 1),
            ("2020", 1),
            ("2030", 1),
            ("2041", 1),
            ("2042", 1),
            ("2043", 1),
            ("2045", 1),
            ("2050", 1),
            ("2055", 1),
            ("2080", -1),
            ("2095", -1),
            ("2096", 1),
            ("2097", 1),
            ("2098", 1),
        ],
    },

    {
        "kontrollid": "kontroll_langsiktig_gjeld",
        "tema": "Balanse",
        "kategori": "H",
        "skildring": "Langsiktig gjeld stemmer ikke",
        "lhs": "sumLangsiktigGjeld",
        "threshold": 1000,
        "terms": [
            ("2100", 1),
            ("2120", 1),
            ("2130", 1),
            ("2160", 1),
            ("2180", 1),
            ("2185", 1),
            ("2200", 1),
            ("2210", 1),
            ("2220", 1),
            ("2250", 1),
            ("2260", 1),
            ("2280", 1),
            ("2290", 1),
        ],
    },

    {
        "kontrollid": "kontroll_kortsiktig_gjeld",
        "tema": "Balanse",
        "kategori": "H",
        "skildring": "Kortsiktig gjeld stemmer ikke",
        "lhs": "sumKortsiktigGjeld",
        "threshold": 1000,
        "terms": [
            ("2310", 1),
            ("2320", 1),
            ("2330", 1),
            ("2380", 1),
            ("2400", 1),
            ("2460", 1),
            ("2470", 1),
            ("2500", 1),
            ("2510", 1),
            ("2600", 1),
            ("2740", 1),
            ("2770", 1),
            ("2790", 1),
            ("2800", 1),
            ("2900", 1),
            ("2910", 1),
            ("2920", 1),
            ("2949", 1),
            ("2950", 1),
            ("2970", 1),
            ("2980", 1),
            ("2981", 1),
            ("2990", 1),
        ],
    },

    {
        "kontrollid": "kontroll_gjeld_og_egenkapital",
        "tema": "Balanse",
        "kategori": "H",
        "skildring": "Gjeld og egenkapital stemmer ikke",
        "lhs": "sumGjeldOgEgenkapital",
        "threshold": 1000,
        "terms": [
            ("sumEgenkapital", 1),
            ("sumLangsiktigGjeld", 1),
            ("sumKortsiktigGjeld", 1),
        ],
    },

    {
        "kontrollid": "kontroll_ubalanse",
        "tema": "Balanse",
        "kategori": "H",
        "skildring": "Balanse stemmer ikke",
        "lhs": "sumGjeldOgEgenkapital",
        "threshold": 1000,
        "terms": [
            ("sumBalanseverdiForEiendel", 1),
        ],
    },

]


def build_field_to_controls(rules: list[dict]) -> Dict[str, List[str]]:
    """
    Lager mapping fra felt → kontrollid automatisk fra CONTROL_RULES.
    """

    mapping: dict[str, set[str]] = defaultdict(set)

    for rule in rules:
        kontrollid = rule["kontrollid"]

        lhs = rule.get("lhs")
        if lhs:
            mapping[lhs].add(kontrollid)

        for field, _sign in rule.get("terms", []):
            mapping[field].add(kontrollid)

    return {
        field: sorted(list(ctrls))
        for field, ctrls in mapping.items()
    }


FIELD_TO_CONTROLS: Dict[str, List[str]] = build_field_to_controls(CONTROL_RULES)

def get_controls_for_field(field: str) -> List[str]:
    return FIELD_TO_CONTROLS.get(field, [])


def get_rule_by_id(kontrollid: str,) -> Optional[dict]:
    for rule in CONTROL_RULES:
        if rule["kontrollid"] == kontrollid:
            return rule

    return None