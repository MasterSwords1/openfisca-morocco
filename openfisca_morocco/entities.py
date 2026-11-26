"""This file defines the entities needed by our legislation.

Taxes and benefits can be calculated for different entities: persons, household,
companies, etc.

See https://openfisca.org/doc/key-concepts/person,_entities,_role.html
"""

from openfisca_core.entities import build_entity

Household = build_entity(
    key="household",
    plural="households",
    label="All the people in a family or group who live together in the same place.",
    doc="""
    Household is an example of a group entity.
    A group entity contains one or more individuals.
    Each individual in a group entity has a role (e.g. parent or children).
    Some roles can only be held by a limited number of individuals (e.g. a
    'first_parent' can only be held by one individual), while others can
    have an unlimited number of individuals (e.g. 'children').

    Example:
        Family variables (e.g. allocations familiales) are usually defined for a
        group entity such as 'Household'.

    Usage:
        Check the number of individuals of a specific role (e.g. check if there
        is an 'adult' with household.nb_persons(Household.ADULT)).
        Calculate a variable applied to each individual of the group entity
        (e.g. calculate the 'salaire_brut_global' of each member of the
        'Household' with:
            salaires = household.members("salaire_brut_global", period = YEAR)
            total_salaires = household.sum(salaires)).

    For more information, see: https://openfisca.org/doc/coding-the-legislation/50_entities.html
    """,
    roles=[
        {
            "key": "adult",
            "plural": "adults",
            "label": "Adult",
            "doc": "The adults of the household.",
        },
        {
            "key": "child",
            "plural": "children",
            "label": "Child",
            "doc": "The dependants of the household (children, students and disabled adult children). The role describes dependency, not age.",
        },
    ],
)

Company = build_entity(
    key="company",
    plural="companies",
    label="An enterprise that files its own tax declarations.",
    doc="""
    Company is the entity on which business taxes are computed. Moroccan VAT
    (TVA) is declared by the enterprise, not by the individual who owns it, so
    the TVA variables live on this entity and use monthly periods (the tax is
    declared monthly, CGI articles 112 and following).

    Company declares a single role, ``membre``, because an OpenFisca group
    entity cannot be instantiated without one: the simulation builder needs a
    role to attach people to. The role is a modelling necessity, not a legal
    claim — it says "this person is recorded against this company", and **no
    formula in this package reads it**. Employees, directors and shareholders
    are therefore not modelled as such, and no figure is aggregated over them.

    Usage:
        enterprise("tva_nette_a_payer", "2024-06") computes the VAT due by one
        company for June 2024.

    For more information, see: https://openfisca.org/doc/coding-the-legislation/50_entities.html
    """,
    roles=[
        {
            "key": "membre",
            "plural": "membres",
            "label": "Personne rattachée à l'entreprise",
            "doc": (
                "Rattachement administratif utilisé par le moteur de simulation. "
                "Aucune formule de ce package n'agrège de montant sur ce rôle."
            ),
        },
    ],
)

Person = build_entity(
    key="person",
    plural="persons",
    label="An individual. The minimal entity on which legislation can be applied.",
    doc="""
    Variables like 'salaire_brut_global' and 'impot_sur_le_revenu' are usually
    defined for the entity 'Person'.

    Usage:
        Calculate a variable applied to a 'Person' (e.g. access the
        'salaire_brut_global' of a specific year with
        person("salaire_brut_global", "2025")).

    For more information, see: https://openfisca.org/doc/coding-the-legislation/50_entities.html
    """,
    is_person=True,
)

entities = [Household, Company, Person]
