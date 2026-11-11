install:
	uv run --locked pre-commit install

test:
	uv run openfisca test --country-package openfisca_morocco openfisca_morocco/tests

serve-local:
	uv run openfisca serve --country-package openfisca_morocco
