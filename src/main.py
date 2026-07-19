"""Entry point for the CrewAI Jira → Developer → Reviewer flow."""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .crew import JiraDevFlow

load_dotenv()

OUTPUT_DIR = Path("output")


def run():
    """Run the Jira Dev Flow."""
    jira_task_key = os.getenv("JIRA_TASK_KEY", "")

    if not jira_task_key:
        # Check if passed as CLI argument
        if len(sys.argv) > 1:
            jira_task_key = sys.argv[1]
        else:
            print("Error: No Jira task key provided.")
            print("Set JIRA_TASK_KEY env var or pass as argument:")
            print("  python -m src.main PROJ-123")
            sys.exit(1)

    print(f"Starting Jira Dev Flow for task: {jira_task_key}")
    print("-" * 50)

    flow = JiraDevFlow(jira_task_key=jira_task_key)
    result = flow.kickoff()

    # Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"{jira_task_key}_{timestamp}.md"

    output_content = f"""# Flow Result: {jira_task_key}

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
