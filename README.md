# CrewAI Project

A multi-agent AI project built with [CrewAI](https://github.com/crewAIInc/crewAI), containerized with Docker for easy deployment.

## Project Structure

```
crewai-project/
├── src/
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── crew.py          # Crew assembly
│   ├── agents.py        # Agent definitions
│   └── tasks.py         # Task definitions
├── config/
│   ├── agents.yaml      # Agent config (reference)
│   └── tasks.yaml       # Task config (reference)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
└── .dockerignore
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- An OpenAI API key (or another LLM provider key supported by CrewAI)

### Setup

1. Copy the environment file and add your API key:

   ```bash
   cp .env.example .env
   # Edit .env and set your OPENAI_API_KEY
   ```

2. (Optional) Customize the topic in `.env`:

   ```
   CREW_TOPIC=Your custom research topic here
   ```

### Running with Docker

Build and run the container:

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up --build -d
docker compose logs -f crewai
```

### Running Locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m src.main
```

## Customization

- **Agents**: Modify `src/agents.py` to add or change agents.
- **Tasks**: Modify `src/tasks.py` to define new workflows.
- **Crew**: Modify `src/crew.py` to change the process type (sequential, hierarchical) or add more agents/tasks.
- **Config**: The `config/` YAML files serve as a reference for agent/task definitions and can be integrated with CrewAI's YAML-based configuration if preferred.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `OPENAI_MODEL_NAME` | No | Override the default model (e.g., `gpt-4o`) |
| `CREW_TOPIC` | No | The topic for the crew to research |
