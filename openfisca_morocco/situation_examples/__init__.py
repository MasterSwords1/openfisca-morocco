"""This file provides a function to load json example situations."""

import json
import os

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


def parse(file_name):
    """Load json example situations."""
    file_path = os.path.join(DIR_PATH, file_name)
    with open(file_path, encoding="utf8") as file:
        return json.loads(file.read())


salarie = parse("salarie.json")
salarie_exonere = parse("salarie_exonere.json")
salarie_impose = parse("salarie_impose.json")
couple_avec_enfants = parse("couple_avec_enfants.json")
haut_revenu = parse("haut_revenu.json")
cout_employeur = parse("cout_employeur.json")
menage_asd = parse("menage_asd.json")
