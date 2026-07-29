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
            "@aashari/mcp-server-atlassian-jira",
        ],
        "env": {
            "ATLASSIAN_SITE_NAME": os.environ.get("JIRA_BASE_URL", "").replace("https://", "").replace(".atlassian.net", ""),
            "ATLASSIAN_USER_EMAIL": os.environ.get("JIRA_EMAIL", ""),
            "ATLASSIAN_API_TOKEN": os.environ.get("JIRA_API_TOKEN", ""),
        },
    }


def get_datadog_mcp_config() -> dict[str, Any]:
    """DataDog MCP server configuration (stdio transport)."""
    return {
        "type": "stdio",
        "command": "npx",
        "args": [
            "-y",
            "@winor30/mcp-server-datadog",
        ],
        "env": {
            "DATADOG_API_KEY": os.environ.get("DD_API_KEY", ""),
            "DATADOG_APP_KEY": os.environ.get("DD_APP_KEY", ""),
            "DATADOG_SITE": os.environ.get("DD_SITE", "datadoghq.com"),
        },
    }


def get_gitlab_mcp_config() -> dict[str, Any]:
    """GitLab MCP server configuration (stdio transport)."""
    return {
        "type": "stdio",
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-gitlab",
        ],
        "env": {
            "GITLAB_PERSONAL_ACCESS_TOKEN": os.environ.get("GITLAB_TOKEN", ""),
            "GITLAB_API_URL": os.environ.get("GITLAB_URL", "https://gitlab.com") + "/api/v4",
        },
    }
