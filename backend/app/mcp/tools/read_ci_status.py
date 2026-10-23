"""MCP Tool: read_ci_status.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Retrieves latest GitHub Actions workflow runs, statuses, failed jobs,
and failing steps for a repository branch or commit.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.exceptions import (
    GitlexaException,
    MCPToolExecutionError,
    ValidationError,
)
from app.core.logging import logger
from app.github.client import GitHubClient
from app.github.workflows import GitHubWorkflows
from app.mcp.tools.list_issues import parse_repo_identifier


async def read_ci_status(
    repo: str,
    branch: Optional[str] = None,
    sha: Optional[str] = None,
    client: Optional[GitHubClient] = None,
) -> Dict[str, Any]:
    """MCP tool to retrieve CI intelligence and blocker statuses.

    Args:
        repo: Repository identifier ('owner/repo' or GitHub URL).
        branch: Optional Git branch name (e.g. 'main').
        sha: Optional commit SHA.
        client: Optional pre-configured GitHubClient for testing or custom auth.

    Returns:
        Structured dictionary with CI summary, failure flags, and failed jobs.

    Raises:
        ValidationError: If repo identifier is invalid.
        MCPToolExecutionError: If execution fails unexpectedly.
    """
    owner, repo_name = parse_repo_identifier(repo)

    try:
        workflows_api = GitHubWorkflows(client=client)
        summary = await workflows_api.get_ci_summary(
            owner=owner,
            repo=repo_name,
            branch=branch,
            sha=sha,
        )
        return summary

    except GitlexaException:
        raise
    except Exception as exc:
        logger.error("Failed to execute read_ci_status for %s/%s: %s", owner, repo_name, exc)
        raise MCPToolExecutionError(
            tool_name="read_ci_status",
            message=str(exc),
            details={"repo": repo, "branch": branch, "sha": sha},
        ) from exc
