import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

from openfisca_morocco import CountryTaxBenefitSystem

PARAMETERS = Path(__file__).parents[1] / "parameters"
ALLOWED_PARAMETER_HOSTS = {
    "www.sgg.gov.ma",
    "www.anss.gov.ma",
    "www.cnss.ma",
    "www.emploi.gov.ma",
}
# Variables may cite the competent public authority when no gazette URL is
# encoded, but never a private corpus or a code host.
ALLOWED_VARIABLE_HOSTS = ALLOWED_PARAMETER_HOSTS | {
    "www.tax.gov.ma",
    "maloi.ma",
    "www.acaps.ma",
}
PRIVATE_MARKERS = ("morocco-holy-graph", "github.com", "/corpus/")
PAGE_FRAGMENT = re.compile(r"#page=", re.IGNORECASE)
ANNUAL_LAW = re.compile(r"\b(?:Loi de finances|Décrets?)\b")


def _reference_lists(node):
    """Yield reference lists, including a single object or URL reference."""
    if isinstance(node, dict):
        metadata = node.get("metadata")
        if isinstance(metadata, dict) and "reference" in metadata:
            reference = metadata["reference"]
            if isinstance(reference, list):
                yield reference
            elif isinstance(reference, (dict, str)):
                yield [reference]
        for value in node.values():
            yield from _reference_lists(value)
    elif isinstance(node, list):
        for value in node:
            yield from _reference_lists(value)


def _hrefs(references):
    return [
        reference.get("href", "") if isinstance(reference, dict) else str(reference)
        for reference in references
    ]


def _is_private(href):
    return any(marker in href.lower() for marker in PRIVATE_MARKERS)


def test_parameter_reference_policy():
    checked = 0
    for path in PARAMETERS.rglob("*.yaml"):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for references in _reference_lists(document):
            assert references, path
            hrefs = _hrefs(references)
            assert all(hrefs), path
            hosts = [urlparse(href).hostname for href in hrefs]
            assert all(host in ALLOWED_PARAMETER_HOSTS for host in hosts), (
                path,
                hosts,
            )
            assert not any(_is_private(href) for href in hrefs), path
            if "www.sgg.gov.ma" in hosts:
                assert hosts[0] == "www.sgg.gov.ma", path
            titles = [
                reference.get("title", "") if isinstance(reference, dict) else ""
                for reference in references
            ]
            has_cgi = any("Code Général des Impôts" in title for title in titles)
            has_annual_law = any(ANNUAL_LAW.search(title) for title in titles)
            if has_cgi and has_annual_law:
                assert ANNUAL_LAW.search(titles[0]), (path, titles)
            for href in hrefs:
                if PAGE_FRAGMENT.search(href):
                    assert href.lower().count("#page=") == 1, (path, href)
                    fragment = re.split(
                        r"#page=", href, maxsplit=1, flags=re.IGNORECASE
                    )[1]
                    assert fragment.isdigit() and int(fragment) > 0, (path, href)
            checked += len(hrefs)
    assert checked > 0


def test_variable_references_are_public():
    checked = 0
    for name, variable in CountryTaxBenefitSystem().variables.items():
        reference = getattr(variable, "reference", None)
        if not reference:
            continue
        hrefs = [reference] if isinstance(reference, str) else list(reference)
        for href in hrefs:
            host = urlparse(str(href)).hostname
            assert host in ALLOWED_VARIABLE_HOSTS, (name, href)
            assert not _is_private(str(href)), (name, href)
            checked += 1
    assert checked > 0
