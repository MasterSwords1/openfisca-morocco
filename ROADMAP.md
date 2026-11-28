# Roadmap

**Current release:** 0.18.0 — 160 parameters, 175 variables, IR, IS, TVA,
CNSS/AMO contributions, the Code du travail, registration duties, direct
social assistance, two reforms, per-domain documentation and a self-hosted
Legislation Explorer.

The roadmap is tracked with **GitHub milestones**. Each phase is a milestone;
each unit of work is an issue with acceptance criteria. A phase closes when its
issues are closed, not when a date passes.

## Principles

- **Official sources only.** Every parameter cites an official publisher
  (SGG gazette, ANSS, CNSS, emploi, DGI); no private corpus link reaches the
  public package or the API.
- **Date every value.** A rate without an effective date is not a model.
- **Tests are the contract.** A behaviour without a test is a claim, not a
  feature.
- **Small, reviewable changes.** One behaviour per pull request.

## Milestones

### v0.19 — Release & hardening

Make the package installable and keep it installable.

| Issue | Work |
|---|---|
| #62 | Publish 0.18.0 to PyPI via trusted publishing |
| #63 | Bound `openfisca-core` and test min/max in CI |
| #72 | Document parameters in the YAML (`documentation`/`notes`) |
| #64 | Add a parameter schema test |
| #73 | Add tutorial notebooks for simulation, reforms and the API |
| #65 | Anchor the model on public real-world cases |

### v0.20 — Benefits & Explorer

Close the two cheapest citizen-facing gaps, finish the Explorer navigation and
the contributor documentation.

| Issue | Work |
|---|---|
| #66 | Model the unemployment benefit (IPE) |
| #67 | Model inheritance and donation duties |
| #68 | Group Explorer variables by domain |
| #69 | Add a French contributor guide and keep the roadmap current |

### v0.21 — Pension & local taxes

The two heaviest remaining domains; both need source-backed parameter datasets
before implementation.

| Issue | Work |
|---|---|
| #70 | Model CNSS and RCAR retirement pensions |
| #71 | Model local taxes: national framework and commune rate gap |

### v1.0 — Complete & usable

| Issue | Work |
|---|---|
| #74 | Model excise duties and price-compensation rates |
| #75 | Assess survey-based microsimulation (CEQ-style) |
| #12 | Release v1.0.0: public repo, PyPI, tag |
| #13 | List the package in OpenFisca community channels |

## Not planned for now

These are deliberately out of scope, not forgotten:

- **Health reimbursement (AMO acts).** Needs a care basket and tariffs; the
  cost is disproportionate to the value for a tax-benefit model.
- **Public-sector pay scales.** HR-specific, not a household tax-benefit rule.
- **Individual survey microdata.** Requires a data-partner agreement and a
  licence; #75 assesses feasibility before any implementation.

## How work is tracked

| Label | Meaning |
|---|---|
| `release` | Publishing, tags, packaging |
| `engineering` | Tooling, CI, tests, refactors |
| `documentation` | Guides, notebooks, reference pages |
| `legislation` | New rules and parameters from official sources |
| `enhancement` | Explorer and user-facing improvements |
| `stretch` | Worth doing, not committed to a phase |

An issue is done when its acceptance boxes are checked, `make test` passes and
the change is merged. A milestone is done when all of its issues are closed.

## Releasing

See [`docs/releasing.md`](docs/releasing.md) for the trusted-publishing setup,
the dispatch command and the verification steps.
