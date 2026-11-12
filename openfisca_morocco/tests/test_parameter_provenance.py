"""Every parameter value must cite the legal source it comes from.

A parameter is a number that a legislator published somewhere. If the package
cannot say where, the number is a guess, and a simulation built on it is not
evidence of anything.

The gate walks every file under ``openfisca_morocco/parameters`` with the
OpenFisca parameter loader (so an invalid parameter file fails here too) and
requires each **leaf** value to resolve a non-empty ``metadata.reference``.

A reference may be declared on the leaf itself or on any of its ancestors in
the same file: a scale is legally one article, so repeating the article on each
of its brackets would be noise, not rigour. What is forbidden is a leaf that
resolves nothing at all.

Each reference must name the instrument (``title``) and where to read it
(``href``) when written in the structured form, so that a bare URL with no
instrument is not accepted either.

Run it with the rest of the suite::

    make test

See issue #4.
"""

from pathlib import Path

import pytest
from openfisca_core.parameters import (
    Parameter,
    ParameterScale,
    load_parameter_file,
)

PARAMETERS_DIR = Path(__file__).resolve().parent.parent / "parameters"
PARAMETER_FILES = sorted(PARAMETERS_DIR.rglob("*.yaml"))


def _iter_leaves(node, path, inherited_reference):
    """Yield ``(path, resolved_reference)`` for every leaf value of ``node``.

    ``inherited_reference`` is the closest reference declared by an ancestor,
    which a leaf without its own reference inherits.
    """
    reference = (node.metadata or {}).get("reference") or inherited_reference

    if isinstance(node, Parameter):
        yield path, reference
    elif isinstance(node, ParameterScale):
        for index, bracket in enumerate(node.brackets, start=1):
            yield from _iter_leaves(bracket, f"{path}[{index}]", reference)
    else:
        for child_name, child in node.children.items():
            yield from _iter_leaves(child, f"{path}.{child_name}", reference)


def _reference_problems(reference):
    """Return the reasons a reference is not acceptable (empty when it is)."""
    if not reference:
        return ["no reference"]

    references = reference if isinstance(reference, list) else [reference]

    problems = []
    for item in references:
        if isinstance(item, str):
            if not item.strip():
                problems.append("empty reference string")
            continue
        if not isinstance(item, dict):
            problems.append(f"unexpected reference type: {type(item).__name__}")
            continue
        if not str(item.get("title", "")).strip():
            problems.append(f"reference without a title: {item!r}")
        if not str(item.get("href", "")).strip():
            problems.append(f"reference without an href: {item!r}")

    return problems


@pytest.mark.parametrize(
    "parameter_file",
    PARAMETER_FILES,
    ids=[str(path.relative_to(PARAMETERS_DIR)) for path in PARAMETER_FILES],
)
def test_every_parameter_cites_its_legal_source(parameter_file):
    # Loading with OpenFisca also checks that the file is a valid parameter
    # file: a malformed YAML parameter must not slip through this gate.
    root = load_parameter_file(str(parameter_file))

    failures = []
    for path, reference in _iter_leaves(root, parameter_file.stem, None):
        problems = _reference_problems(reference)
        if problems:
            failures.append(f"{path}: {', '.join(problems)}")

    assert not failures, (
        f"{parameter_file.relative_to(PARAMETERS_DIR)} has parameter values with "
        "no traceable legal source.\n"
        "Add a `metadata.reference` (title + href) to the parameter or to its "
        "closest ancestor:\n  " + "\n  ".join(failures)
    )


def test_the_gate_has_parameters_to_check():
    """Guard against the gate silently passing because it found no file."""
    assert PARAMETER_FILES, f"no parameter file found under {PARAMETERS_DIR}"
