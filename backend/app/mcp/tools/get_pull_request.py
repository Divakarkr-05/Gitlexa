"""MCP Tool: get_pull_request.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Retrieves comprehensive details for a pull request, including branch tracking,
mergeability, changed files summary, review states, linked issue references,
and CI status.
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
from app.github.pull_requests import GitHubPullRequests
from app.mcp.tools.list_issues import parse_repo_identifier


async def get_pull_request(
    repo: str,
    pr_number: int,
    include_ci: bool = True,
    include_files: bool = True,
    include_reviews: bool = True,
    client: Optional[GitHubClient] = None,
) -> Dict[str, Any]:
    """MCP tool to retrieve full intelligence on a pull request.

    Args:
        repo: Repository identifier ('owner/repo' or GitHub URL).
        pr_number: Pull request number.
        include_ci: Whether to query CI check runs and commit status. Defaults to True.
        include_files: Whether to include changed files diff summary. Defaults to True.
        include_reviews: Whether to include review states. Defaults to True.
        client: Optional pre-configured GitHubClient for testing or custom auth.

    Returns:
        Structured dictionary with PR intelligence.

    Raises:
        ValidationError: If input arguments fail validation.
        ResourceNotFoundError: If the PR does not exist on GitHub.
        MCPToolExecutionError: If execution fails unexpectedly.
    """
    owner, repo_name = parse_repo_identifier(repo)

    if not isinstance(pr_number, int) or pr_number < 1:
        raise ValidationError(
            message=f"Invalid PR number '{pr_number}'. Must be a positive integer.",
            details={"repo": repo, "pr_number": pr_number},
        )

    try:
        pr_api = GitHubPullRequests(client=client)
        details = await pr_api.get_pull_request_details(
            owner=owner,
            repo=repo_name,
            pull_number=pr_number,
            include_ci=include_ci,
            include_files=include_files,
            include_reviews=include_reviews,
        )
        return details

    except GitlexaException:
        raise
    except Exception as exc:
        logger.error("Failed to execute get_pull_request for %s/%s PR #%d: %s", owner, repo_name, pr_number, exc)
        raise MCPToolExecutionError(
            tool_name="get_pull_request",
            message=str(exc),
            details={"repo": repo, "pr_number": pr_number},
        ) from exc
