"""CrewAI Flow: Jira Task Analyzer → Developer → MR Reviewer.

This module defines a Flow with conditional routing:
- Analyzer decides if dev work is needed, info is missing, or no action required.
- Developer implements changes and creates a merge request.
- Reviewer approves or requests changes (loops back to developer if needed).
"""

import json
import os
from pathlib import Path
from typing import Any

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.flow.flow import Flow, listen, router, start
from pydantic import BaseModel

from .tools import get_datadog_mcp_config, get_jira_mcp_config


# --- State ---


class FlowState(BaseModel):
    """Shared state across the flow."""

    jira_project: str = ""
    jira_task_key: str = ""
    analysis_result: dict[str, Any] = {}
    dev_result: dict[str, Any] = {}
    review_result: dict[str, Any] = {}
    review_iteration: int = 0
    final_status: str = ""
    message: str = ""


# --- Helpers ---


def load_flow_config() -> dict[str, Any]:
    """Load flow.yaml configuration."""
    config_path = Path(__file__).parent / "config" / "flow.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_agents_config() -> dict[str, Any]:
    """Load agents.yaml configuration."""
    config_path = Path(__file__).parent / "config" / "agents.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_tasks_config() -> dict[str, Any]:
    """Load tasks.yaml configuration."""
    config_path = Path(__file__).parent / "config" / "tasks.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def format_project_paths(flow_config: dict) -> str:
    """Format project info for agent context."""
    projects = flow_config.get("projects", [])
    workspace_dir = flow_config.get("workspace_dir", "/workspace")
    lines = []
    for p in projects:
        gitlab_ref = p["gitlab_ref"]
        project_name = gitlab_ref.split("/")[-1]
        local_path = f"{workspace_dir}/{project_name}"
        lines.append(
            f"- GitLab: {gitlab_ref} | Local clone: {local_path} | Description: {p['description']}"
        )
    return "\n".join(lines)


def parse_json_output(output: str) -> dict[str, Any]:
    """Parse JSON from agent output, handling markdown code blocks."""
    text = output.strip()
    if text.startswith("```"):
        # Remove markdown code fences
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


# --- Flow ---


class JiraDevFlow(Flow[FlowState]):
    """Main flow orchestrating the Jira → Dev → Review pipeline."""

    def __init__(self, jira_project: str, **kwargs):
        super().__init__(**kwargs)
        self.state.jira_project = jira_project
        self._flow_config = load_flow_config()
        self._agents_config = load_agents_config()
        self._tasks_config = load_tasks_config()

    # --- Step 1: Analyze Jira Task ---

    @start()
    def analyze_task(self) -> str:
        """Analyze the Jira task and determine the outcome."""
        agents_cfg = self._agents_config["task_analyzer"]
        tasks_cfg = self._tasks_config["analyze_jira_task"]

        agent = Agent(
            role=agents_cfg["role"],
            goal=agents_cfg["goal"],
            backstory=agents_cfg["backstory"],
            llm=agents_cfg.get("llm"),
            verbose=agents_cfg.get("verbose", True),
            mcps=[
                get_jira_mcp_config(),
                get_datadog_mcp_config(),
            ],
        )

        project_paths = format_project_paths(self._flow_config)

        task = Task(
            description=tasks_cfg["description"].format(
                jira_project=self.state.jira_project,
                project_paths=project_paths,
            ),
            expected_output=tasks_cfg["expected_output"],
            agent=agent,
        )

        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()

        try:
            self.state.analysis_result = parse_json_output(str(result))
        except (json.JSONDecodeError, ValueError):
            self.state.analysis_result = {
                "outcome": "insufficient_info",
                "summary": str(result),
                "details": "Could not parse analyzer output as JSON.",
            }

        # Store the resolved task key from analyzer output
        self.state.jira_task_key = self.state.analysis_result.get("jira_task_key", "")

        return self.state.analysis_result.get("outcome", "insufficient_info")

    # --- Router: Decide next step based on analysis ---

    @router(analyze_task)
    def route_analysis(self) -> str:
        """Route based on analysis outcome."""
        outcome = self.state.analysis_result.get("outcome", "insufficient_info")
        if outcome == "action_needed":
            return "action_needed"
        elif outcome == "no_dev_needed":
            return "no_dev_needed"
        else:
            return "insufficient_info"

    # --- Dead ends ---

    @listen("insufficient_info")
    def handle_insufficient_info(self) -> str:
        """Notify user that more information is needed."""
        self.state.final_status = "stopped_insufficient_info"
        self.state.message = (
            f"Task {self.state.jira_task_key} cannot be processed.\n"
            f"Reason: Insufficient information.\n"
            f"Details: {self.state.analysis_result.get('details', 'N/A')}"
        )
        print(f"\n{'='*50}")
        print("FLOW STOPPED: Insufficient information")
        print(f"{'='*50}")
        print(self.state.message)
        return self.state.message

    @listen("no_dev_needed")
    def handle_no_dev_needed(self) -> str:
        """Notify user that no development is needed."""
        self.state.final_status = "stopped_no_dev_needed"
        self.state.message = (
            f"Task {self.state.jira_task_key} does not require development.\n"
            f"Summary: {self.state.analysis_result.get('summary', 'N/A')}\n"
            f"Details: {self.state.analysis_result.get('details', 'N/A')}"
        )
        print(f"\n{'='*50}")
        print("FLOW STOPPED: No development needed")
        print(f"{'='*50}")
        print(self.state.message)
        return self.state.message

    # --- Step 2: Develop ---

    @listen("action_needed")
    def develop(self) -> str:
        """Implement changes and create a merge request."""
        return self._run_developer()

    def _run_developer(self, review_feedback: str | None = None) -> str:
        """Run the developer agent (initial or fix iteration)."""
        agents_cfg = self._agents_config["developer"]

        agent = Agent(
            role=agents_cfg["role"],
            goal=agents_cfg["goal"],
            backstory=agents_cfg["backstory"],
            llm=agents_cfg.get("llm"),
            verbose=agents_cfg.get("verbose", True),
        )

        analysis = self.state.analysis_result

        # Resolve gitlab project path from flow config
        gitlab_project_path = analysis.get("gitlab_project_path", "")
        workspace_dir = self._flow_config.get("workspace_dir", "/workspace")
        for project in self._flow_config.get("projects", []):
            if project["gitlab_ref"] == gitlab_project_path:
                break
            # Also match if analyzer returned the project name or local path
            project_name = project["gitlab_ref"].split("/")[-1]
            local_path = f"{workspace_dir}/{project_name}"
            if analysis.get("project_path") in (project["gitlab_ref"], local_path, project_name):
                gitlab_project_path = project["gitlab_ref"]
                break

        if review_feedback:
            # Fix iteration
            tasks_cfg = self._tasks_config["implement_review_fixes"]
            project_name = gitlab_project_path.split("/")[-1]
            task = Task(
                description=tasks_cfg["description"].format(
                    merge_request_url=self.state.dev_result.get("merge_request_url", ""),
                    merge_request_iid=self.state.dev_result.get("merge_request_iid", ""),
                    review_feedback=review_feedback,
                    branch_name=self.state.dev_result.get("branch_name", ""),
                    gitlab_project_path=gitlab_project_path,
                    project_name=project_name,
                ),
                expected_output=tasks_cfg["expected_output"],
                agent=agent,
            )
        else:
            # Initial implementation
            tasks_cfg = self._tasks_config["implement_changes"]
            project_name = gitlab_project_path.split("/")[-1]
            local_path = f"{workspace_dir}/{project_name}"
            task = Task(
                description=tasks_cfg["description"].format(
                    project_path=local_path,
                    task_summary=analysis.get("summary", ""),
                    task_details=analysis.get("details", ""),
                    affected_files=", ".join(analysis.get("affected_files", [])),
                    jira_task_key=self.state.jira_task_key,
                    gitlab_project_path=gitlab_project_path,
                ),
                expected_output=tasks_cfg["expected_output"],
                agent=agent,
            )

        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()

        try:
            self.state.dev_result = parse_json_output(str(result))
        except (json.JSONDecodeError, ValueError):
            self.state.dev_result = {
                "merge_request_url": "",
                "changes_summary": str(result),
                "gitlab_project_path": gitlab_project_path,
            }

        return "dev_complete"

    # --- Step 3: Review ---

    @listen(develop)
    def review(self) -> str:
        """Review the merge request."""
        return self._run_review()

    def _run_review(self) -> str:
        """Run the reviewer agent."""
        self.state.review_iteration += 1
        max_iterations = self._flow_config.get("max_review_iterations", 3)

        agents_cfg = self._agents_config["mr_reviewer"]
        tasks_cfg = self._tasks_config["review_merge_request"]

        agent = Agent(
            role=agents_cfg["role"],
            goal=agents_cfg["goal"],
            backstory=agents_cfg["backstory"],
            llm=agents_cfg.get("llm"),
            verbose=agents_cfg.get("verbose", True),
        )

        task = Task(
            description=tasks_cfg["description"].format(
                merge_request_url=self.state.dev_result.get("merge_request_url", ""),
                gitlab_project_path=self.state.dev_result.get("gitlab_project_path", ""),
                merge_request_iid=self.state.dev_result.get("merge_request_iid", ""),
            ),
            expected_output=tasks_cfg["expected_output"],
            agent=agent,
        )

        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()

        try:
            self.state.review_result = parse_json_output(str(result))
        except (json.JSONDecodeError, ValueError):
            self.state.review_result = {
                "outcome": "approved",
                "feedback": str(result),
            }

        outcome = self.state.review_result.get("outcome", "approved")

        if outcome == "approved":
            self.state.final_status = "completed"
            self.state.message = (
                f"Merge request approved!\n"
                f"URL: {self.state.dev_result.get('merge_request_url', 'N/A')}\n"
                f"Task: {self.state.jira_task_key}"
            )
            print(f"\n{'='*50}")
            print("FLOW COMPLETE: Merge request approved")
            print(f"{'='*50}")
            print(self.state.message)
            return self.state.message

        elif outcome == "changes_requested" and self.state.review_iteration < max_iterations:
            # Loop back to developer
            feedback = self.state.review_result.get("feedback", "")
            print(f"\nReview iteration {self.state.review_iteration}: Changes requested")
            print(f"Feedback: {feedback}")
            self._run_developer(review_feedback=feedback)
            return self._run_review()

        else:
            # Max iterations reached
            self.state.final_status = "escalated"
            self.state.message = (
                f"Max review iterations ({max_iterations}) reached.\n"
                f"MR: {self.state.dev_result.get('merge_request_url', 'N/A')}\n"
                f"Last feedback: {self.state.review_result.get('feedback', 'N/A')}\n"
                f"Escalating to human reviewer."
            )
            print(f"\n{'='*50}")
            print("FLOW ESCALATED: Max review iterations reached")
            print(f"{'='*50}")
            print(self.state.message)
            return self.state.message
