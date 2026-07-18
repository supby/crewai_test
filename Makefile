.PHONY: run build up up-d down logs clean docker-run

# Run locally (without Docker)
run:
	python -m src.main

# Build the Docker image
build:
	docker compose build

# Run with docker run (uses local .env for secrets)
docker-run: build
	docker run --rm --env-file .env -v $(PWD)/output:/app/output crewai-app

# Run in Docker via compose (uses local .env for secrets)
up:
	docker compose up --build

# Run in Docker (detached)
up-d:
	docker compose up --build -d

# Stop containers
down:
	docker compose down

# View logs
logs:
	docker compose logs -f crewai

# Remove containers and images
clean:
	docker compose down --rmi local --volumes
