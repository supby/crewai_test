.PHONY: run build up up-d down logs clean docker-run

# Run locally (without Docker)
# Usage: make run TASK=PROJ-123
run:
	python -m src.main $(TASK)

# Build the Docker image
build:
	docker compose build

# Run with docker run (uses local .env for secrets)
# Usage: make docker-run TASK=PROJ-123
docker-run: build
	docker run --rm --env-file .env -v $(PWD)/output:/app/output crewai-jira-dev-flow python -m src.main $(TASK)

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
