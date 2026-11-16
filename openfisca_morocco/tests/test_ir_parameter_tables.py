"""Transcription guard for the art. 40-I coefficients and the duty table.

These tables are long and easy to mistype; the behavioural tests only exercise a
few categories and bands. This test compares the packaged values with the table
read from the CGI 2026 edition, so a changed digit fails the suite.
"""

from pathlib import Path

import yaml

PARAMETERS = (
    Path(__file__).resolve().parent.parent
    / "parameters"
    / "impot_revenu"
    / "regimes_professionnels.yaml"
)

COEFFICIENTS = {
    "alimentation_generale": 0.06,
    "autres_produits_alimentaires": 0.08,
    "matieres_premieres": 0.08,
    "materiaux_construction": 0.08,
    "produits_chimiques": 0.10,
    "autres_produits_non_alimentaires": 0.12,
    "restauration_rapide": 0.10,
    "restaurant_debit_boissons": 0.20,
    "transport": 0.10,
    "entretien": 0.15,
    "location_biens_meubles": 0.20,
    "autres_locations_gestion": 0.25,
    "coiffure_esthetique": 0.20,
    "metiers_techniques": 0.30,
    "autres_artisans_services": 0.12,
    "courtiers": 0.45,
    "autres_prestations": 0.20,
    "fabrication_alimentaire": 0.10,
    "fabrication_non_alimentaire": 0.10,
    "chevillard": 0.04,
    "marchand_tabac": 0.03,
    "marchand_gaz": 0.045,
    "marchand_farine": 0.05,
    "armateur_peche": 0.07,
    "boulanger": 0.08,
}

THRESHOLDS = [500.0, 1000.0, 2500.0, 5000.0, 10000.0, 25000.0, 50000.0]
ANNUAL_DUTIES = [1200.0, 1560.0, 2280.0, 2880.0, 4200.0, 6000.0, 9000.0, 14400.0]


def _value(node):
    return next(iter(node["values"].values()))["value"]


def _load():
    return yaml.safe_load(PARAMETERS.read_text())


def test_coefficients_match_article_40():
    coefficients = _load()["cpu"]["coefficients"]
    assert set(coefficients) - {"description", "metadata"} == set(COEFFICIENTS)
    for name, expected in COEFFICIENTS.items():
        assert _value(coefficients[name]) == expected, name


def test_duty_table_matches_article_73():
    table = _load()["cpu"]["droits_complementaires"]
    for index, expected in enumerate(THRESHOLDS, start=1):
        assert _value(table[f"seuil_{index}"]) == expected
    for index, expected in enumerate(ANNUAL_DUTIES, start=1):
        assert _value(table[f"montant_{index}"]) == expected
