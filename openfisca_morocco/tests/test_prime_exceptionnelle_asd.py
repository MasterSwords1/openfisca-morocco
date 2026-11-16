"""Séquence de consommation de la prime exceptionnelle ASD.

OpenFisca est sans état entre périodes : le nombre de mois restants est une
entrée que l'appelant décrémente. Ce test déroule les séquences que la loi
autorise (douze mois, continus ou non) et vérifie le contrat de décrémentation :
douze mois payés au maximum, rien quand le compteur est épuisé, et refus d'une
valeur supérieure à douze.
"""

from openfisca_core.simulation_builder import SimulationBuilder

from openfisca_morocco import CountryTaxBenefitSystem

SYSTEM = CountryTaxBenefitSystem()


def simulate(months):
    """Renvoie les primes payées pour {période: mois restants}."""
    periods = list(months)
    situation = {
        "persons": {"adulte": {}},
        "households": {
            "famille": {
                "adults": ["adulte"],
                "montant_asd_avant_perte": {p: 800.0 for p in periods},
                "mois_restants_prime_exceptionnelle": months,
            }
        },
    }
    simulation = SimulationBuilder().build_from_dict(SYSTEM, situation)
    return [
        float(simulation.calculate("prime_exceptionnelle_asd", p)[0]) for p in periods
    ]


def test_twelve_continuous_months():
    months = {
        "2026-08": 12,
        "2026-09": 11,
        "2026-10": 10,
        "2026-11": 9,
        "2026-12": 8,
        "2027-01": 7,
        "2027-02": 6,
        "2027-03": 5,
        "2027-04": 4,
        "2027-05": 3,
        "2027-06": 2,
        "2027-07": 1,
    }
    paid = simulate(months)
    assert paid == [800.0] * 12
    assert sum(paid) == 9600.0


def test_thirteenth_month_pays_nothing():
    assert simulate({"2027-08": 0}) == [0.0]


def test_non_continuous_consumption():
    """Six mois payés, deux mois de pause, puis six mois payés."""
    months = {
        "2026-08": 12,
        "2026-09": 11,
        "2026-10": 10,
        "2026-11": 9,
        "2026-12": 8,
        "2027-01": 7,
        "2027-02": 0,
        "2027-03": 0,
        "2027-04": 6,
        "2027-05": 5,
        "2027-06": 4,
        "2027-07": 3,
        "2027-08": 2,
        "2027-09": 1,
    }
    paid = simulate(months)
    assert paid.count(800.0) == 12
    assert sum(paid) == 9600.0


def test_counter_above_twelve_is_refused():
    assert simulate({"2026-08": 13}) == [0.0]
