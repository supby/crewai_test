"""Entry point for the CrewAI Jira → Developer → Reviewer flow."""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .crew import JiraDevFlow, load_flow_config

load_dotenv()

OUTPUT_DIR = Path("output")


def run():
    """Run the Jira Dev Flow."""
    # Resolve Jira project: CLI arg > env var > flow.yaml default
    jira_project = ""
    if len(sys.argv) > 1:
        jira_project = sys.argv[1]
    else:
        jira_project = os.getenv("JIRA_PROJECT", "")

    if not jira_project:
        flow_config = load_flow_config()
        jira_project = flow_config.get("jira", {}).get("project", "")

    if not jira_project:
        print("Error: No Jira project provided.")
        print("Set JIRA_PROJECT env var, pass as argument, or configure in flow.yaml:")
        print("  python -m src.main PROJ")
        sys.exit(1)

    print(f"Starting Jira Dev Flow for project: {jira_project}")
    print("Will pick the highest-priority task with 'AI' label.")
    print("-" * 50)

    flow = JiraDevFlow(jira_project=jira_project)
    result = flow.kickoff()

    # Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_key = flow.state.jira_task_key or "no_task"
    output_file = OUTPUT_DIR / f"{jira_project}_{task_key}_{timestamp}.md"

    output_content = f"""# Flow Result: {jira_project} / {task_key}

## Status: {flow.state.final_status}

## Message
{flow.state.message}

## Analysis
{flow.state.analysis_result}

## Development
{flow.state.dev_result}

## Review
{flow.state.review_result}

---
Generated: {timestamp}
"""
    output_file.write_text(output_content)
    print(f"\nOutput saved to: {output_file}")

    return result


if __name__ == "__main__":
    run()
