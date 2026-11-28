# Releasing to PyPI

The package is published by the `Continuous deployment` workflow
(`.github/workflows/cd.yaml`), not from a laptop. The workflow builds, publishes
over PyPI trusted publishing, then pushes the git tag.

## Before you dispatch

1. `pyproject.toml` and `uv.lock` carry the same version, and it is higher than
   any existing tag.
2. `CHANGELOG.md` has an entry for that version.
3. CI is green on `main`.
4. The repository is public and the workflow runs from `main`; the workflow
   refuses anything else.

## One-time PyPI setup (trusted publishing)

Create the project through a **pending publisher** so the first upload can use
OIDC. On <https://pypi.org/manage/account/publishing/>:

| Field | Value |
|---|---|
| PyPI project name | `openfisca-morocco` |
| Owner | `MasterSwords1` |
| Repository name | `openfisca-morocco` |
| Workflow name | `cd.yaml` |
| Environment name | `pypi` |

The values must match exactly; a typo produces `invalid-publisher` at upload
time. The GitHub environment `pypi` already exists and has no protection rules.

An API token is the fallback, not the default: create a project-scoped token on
PyPI and pass it as `UV_PUBLISH_TOKEN` to a manual `uv publish`.

## Dispatch

```sh
gh workflow run cd.yaml --ref main
gh run watch "$(gh run list --workflow cd.yaml --limit 1 --json databaseId -q '.[0].databaseId')"
```

After success the workflow publishes the distributions and pushes the tag
`<version>`.

## Verify

```sh
python -m venv /tmp/of-release
/tmp/of-release/bin/pip install "openfisca-morocco==0.18.0"
/tmp/of-release/bin/python -c "import openfisca_morocco; print(openfisca_morocco.__file__)"
/tmp/of-release/bin/openfisca test --country-package openfisca_morocco \
  "$(/tmp/of-release/bin/python -c 'from pathlib import Path; import openfisca_morocco; print(Path(openfisca_morocco.__file__).parent / "tests")')"
```

Publish pages: <https://pypi.org/project/openfisca-morocco/>.

## Manual fallback

```sh
uv build
uv publish --token "$UV_PUBLISH_TOKEN"
```

Use this only if the workflow is unavailable; it skips the tag step, so push the
tag yourself.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `invalid-publisher` | Pending-publisher fields do not match the repository, workflow or environment |
| `File already exists` | The version was already uploaded; bump it, never reuse it |
| `403` on the environment | The `pypi` environment has a protection rule the run did not satisfy |
| Tag exists | A previous run published this version; bump the version |

## After the release

- Check the README badge and the install command.
- Add the version to `CHANGELOG.md` if it was not already there (it must be).
- Announce on the channels tracked in #13.
