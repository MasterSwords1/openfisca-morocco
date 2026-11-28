install:
	uv run --locked pre-commit install

test:
	uv run openfisca test --country-package openfisca_morocco openfisca_morocco/tests

serve-local:
	uv run openfisca serve --country-package openfisca_morocco

explorer-up:
	docker compose -f explorer/docker-compose.yml up --build -d

explorer-down:
	docker compose -f explorer/docker-compose.yml down

explorer-logs:
	docker compose -f explorer/docker-compose.yml logs -f
