"""Every parameter value must cite the legal source it comes from.

A parameter is a figure a legislator published somewhere. If the package cannot
say where, the figure is a guess, and a simulation built on it is not evidence
of anything.

The gate walks every file under ``openfisca_morocco/parameters`` with the
OpenFisca parameter loader (so an invalid parameter file fails here too) and
requires each **legal object** to carry a valid ``metadata.reference``:

- a leaf parameter must carry the reference itself, or attach one to each of
  its dated values (``values: {2025-01-01: {value: ..., metadata: {reference: ...}}}``),
  which is the form OpenFisca documents for a figure whose source changes over
  time;
- a scale is one legal object (one article fixes all its brackets), so a
  reference on the scale covers its brackets. If the scale has none, each
  bracket value must be sourced individually.

References are deliberately **not** inherited from a parent node: OpenFisca
does not propagate ``metadata``, so a reference declared on a node is invisible
on its children at runtime — and a citation nobody can read next to the number
does not do its job.

A reference must name the instrument (``title``) and where to read it
(``href``), so that a bare URL with no named instrument is not accepted either.

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


def _iter_legal_objects(node, path):
    """Yield ``(path, parameter)`` for the objects that must carry a source.

    A scale with a reference is one object. A scale without one is decomposed
    into its bracket values, so that nothing can hide behind an unsourced
    container.
    """
    if isinstance(node, Parameter):
        yield path, node
    elif isinstance(node, ParameterScale):
        if _has_reference(node):
            yield path, node
        else:
            for index, bracket in enumerate(node.brackets, start=1):
                for name, child in bracket.children.items():
                    yield from _iter_legal_objects(child, f"{path}[{index}].{name}")
    else:
        for child_name, child in node.children.items():
            yield from _iter_legal_objects(child, f"{path}.{child_name}")


def _has_reference(parameter):
    return not _reference_problems((parameter.metadata or {}).get("reference"))


def _reference_problems(reference):
    """Return the reasons a reference is not acceptable (empty when it is)."""
    if not reference:
        return ["no reference"]

    entries = _reference_entries(reference)
    if entries is None:
        return ["malformed reference"]

    problems = []
    for entry in entries:
        if isinstance(entry, str):
            if not entry.strip():
                problems.append("empty reference string")
            continue
        if not isinstance(entry, dict):
            problems.append(f"unexpected reference type: {type(entry).__name__}")
            continue
        if not str(entry.get("title", "")).strip():
            problems.append(f"reference without a title: {entry!r}")
        if not str(entry.get("href", "")).strip():
            problems.append(f"reference without an href: {entry!r}")
    return problems


def _reference_entries(reference):
    """Flatten the accepted reference shapes into a list of entries.

    Accepted shapes: ``"<url>"``, ``{"title": ..., "href": ...}``, a list of
    those, or ``{<date>: {"title": ..., "href": ...}}`` (the date-keyed form
    used when a figure's source changes over time).
    """
    if isinstance(reference, str):
        return [reference]
    if isinstance(reference, dict):
        if "title" in reference or "href" in reference:
            return [reference]
        return list(reference.values())
    if isinstance(reference, list):
        return reference
    return None


def _parameter_problems(parameter):
    """Return the provenance problems of one legal object."""
    problems = _reference_problems((parameter.metadata or {}).get("reference"))
    if not problems:
        return []

    values = getattr(parameter, "values_list", None)
    if not values:
        return problems

    missing = []
    for value in values:
        value_problems = _reference_problems((value.metadata or {}).get("reference"))
        if value_problems:
            missing.append(f"value {value.instant_str}: {', '.join(value_problems)}")

    if not missing:
        return []

    return [
        (
            "no reference on the parameter itself, and the values are not all "
            f"sourced either ({'; '.join(missing)})"
        )
    ]


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
    for path, parameter in _iter_legal_objects(root, parameter_file.stem):
        for problem in _parameter_problems(parameter):
            failures.append(f"{path}: {problem}")

    assert not failures, (
        f"{parameter_file.relative_to(PARAMETERS_DIR)} has parameter values with "
        "no traceable legal source.\n"
        "Add a `metadata.reference` (title + href) to the parameter, or to each "
        "of its dated values:\n  " + "\n  ".join(failures)
    )


def test_the_gate_has_parameters_to_check():
    """Guard against the gate silently passing because it found no file."""
    assert PARAMETER_FILES, f"no parameter file found under {PARAMETERS_DIR}"
