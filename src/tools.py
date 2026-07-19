"""MCP tool configurations for CrewAI agents.

CrewAI supports MCP servers natively via the `mcps` field on agents.
This module provides helper functions to build MCP server configurations
that can be passed to agents programmatically.

The agents use three MCP servers:
- Jira MCP: For reading and managing Jira tasks
- DataDog MCP: For querying metrics, logs, and alerts
- GitLab MCP: For repository operations, MRs, and code review
"""

import os
from typing import Any


def get_jira_mcp_config() -> dict[str, Any]:
    """Jira MCP server configuration (stdio transport)."""
    return {
        "type": "stdio",
        "command": "npx",
        "args": [
            "-y",
            "@anthropic/jira-mcp-server",
        ],
        "env": {
            "JIRA_BASE_URL": os.environ.get("JIRA_BASE_URL", ""),
            "JIRA_EMAIL": os.environ.get("JIRA_EMAIL", ""),
            "JIRA_API_TOKEN": os.environ.get("JIRA_API_TOKEN", ""),
        },
    }


def get_datadog_mcp_config() -> dict[str, Any]:
    """DataDog MCP server configuration (stdio transport)."""
    return {
        "type": "stdio",
        "command": "npx",
        "args": [
            "-y",
            "@anthropic/datadog-mcp-server",
        ],
        "env": {
            "DD_API_KEY": os.environ.get("DD_API_KEY", ""),
            "DD_APP_KEY": os.environ.get("DD_APP_KEY", ""),
            "DD_SITE": os.environ.get("DD_SITE", "datadoghq.com"),
        },
    }


def get_gitlab_mcp_config() -> dict[str, Any]:
    """GitLab MCP server configuration (stdio transport)."""
    return {
        "type": "stdio",
        "command": "npx",
        "args": [
            "-y",
            "@anthropic/gitlab-mcp-server",
        ],
        "env": {
            "GITLAB_TOKEN": os.environ.get("GITLAB_TOKEN", ""),
            "GITLAB_URL": os.environ.get("GITLAB_URL", "https://gitlab.com"),
        },
    }
