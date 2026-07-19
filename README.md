# CrewAI Jira Dev Flow

Automated development pipeline: **Jira Task Analyzer → Developer → MR Reviewer**

Built with [CrewAI Flows](https://docs.crewai.com/concepts/flows), running in Docker.

## Architecture

```
┌─────────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Task Analyzer  │────▶│  Developer  │────▶│  MR Reviewer     │
│  (Jira/DD/GL)   │     │  (GitLab)   │     │  (GitLab)        │
└────────┬────────┘     └──────┬──────┘     └────────┬─────────┘
         │                     │                     │
         ▼                     │                     ▼
   ┌───────────┐               │              ┌───────────┐
   │ Stop:     │               │              │ Approved  │
   │ - no info │               │              │    OR     │
   │ - no dev  │               ◀──────────────│ Changes   │
   └───────────┘           (loop back)        │ Requested │
                                              └───────────┘
```

## Flow Steps

1. **Task Analyzer** — Reads Jira task (with 'AI' tag), checks DataDog metrics, reviews code in GitLab. Outputs:
   - `action_needed` → passes task definition to Developer
   - `insufficient_info` → stops, notifies user
   - `no_dev_needed` → stops, notifies user

2. **Developer** — Implements changes, creates a branch + merge request in GitLab.

3. **MR Reviewer** — Reviews the MR diff. Outputs:
   - `approved` → adds "Approved" comment, notifies user
   - `changes_requested` → loops back to Developer with feedback (max 3 iterations)

## Project Structure

```
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point (CLI + env var)
│   ├── crew.py              # Flow definition with routing
│   ├── tools.py             # MCP server configurations
│   └── config/
│       ├── agents.yaml      # Agent definitions (roles, LLM)
│       ├── tasks.yaml       # Task templates
│       └── flow.yaml        # Project paths, settings
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── requirements.txt
├── .env.example
└── output/                  # Flow results (mounted volume)
```

## Setup

### Prerequisites

- Docker and Docker Compose
- Gemini API key
- Jira API token
- DataDog API + App keys
- GitLab personal access token

### Configuration

1. Copy and fill in secrets:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. Edit `src/config/flow.yaml` to list your local project paths and GitLab project mappings.

3. Mount your project directories in `docker-compose.yml` volumes section.

## Usage

### Run with Docker Compose
```bash
make up
```

### Run with docker run (pass task key)
```bash
make docker-run TASK=PROJ-123
```

### Run locally
```bash
make run TASK=PROJ-123
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `JIRA_BASE_URL` | Yes | Jira instance URL |
| `JIRA_EMAIL` | Yes | Jira account email |
| `JIRA_API_TOKEN` | Yes | Jira API token |
| `DD_API_KEY` | Yes | DataDog API key |
| `DD_APP_KEY` | Yes | DataDog App key |
| `DD_SITE` | No | DataDog site (default: datadoghq.com) |
| `GITLAB_TOKEN` | Yes | GitLab personal access token |
| `GITLAB_URL` | No | GitLab instance URL (default: https://gitlab.com) |
| `JIRA_TASK_KEY` | No | Jira task to process (or pass as CLI arg) |

## Customization

- **LLM**: Change the `llm` field in `src/config/agents.yaml`
- **Projects**: Edit `src/config/flow.yaml` to add/remove project paths
- **MCP servers**: Edit `src/tools.py` to swap MCP server packages
- **Review iterations**: Set `max_review_iterations` in `src/config/flow.yaml`
