"""MCP Tool: list_issues.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Retrieves open or closed issues for a repository with label filtering,
distinguishing ordinary issues from pull requests, and returning structured
records compatible with the Evidence Engine and Agent.
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, List, Optional, Tuple, Union

from app.core.exceptions import (
    GitlexaException,
    MCPToolExecutionError,
    ValidationError,
)
from app.core.logging import logger
from app.github.client import GitHubClient
from app.github.issues import GitHubIssues


def parse_repo_identifier(repo: str) -> Tuple[str, str]:
    """Parse 'owner/repo' or GitHub repository URL into (owner, repo_name).

    Args:
        repo: Repository identifier (e.g. 'octocat/Hello-World' or URL).

    Returns:
        Tuple of (owner, repo_name).

    Raises:
        ValidationError: If the format is invalid or empty.
    """
    if not repo or not isinstance(repo, str):
        raise ValidationError(
            message="Repository identifier must be a non-empty string.",
            details={"repo": repo},
        )

    clean = repo.strip().rstrip("/")
    if clean.endswith(".git"):
        clean = clean[:-4]

    if "github.com/" in clean:
        clean = clean.split("github.com/", 1)[1]

    parts = clean.split("/")
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise ValidationError(
            message=f"Invalid repository format '{repo}'. Expected 'owner/repo' or GitHub URL.",
            details={"repo": repo},
        )

    return parts[0].strip(), parts[1].strip()


async def list_issues(
    repo: str,
    state: str = "open",
    labels: Optional[Union[List[str], str]] = None,
    limit: int = 30,
    client: Optional[GitHubClient] = None,
) -> List[Dict[str, Any]]:
    """MCP tool to list issues for a GitHub repository.

    Args:
        repo: Repository identifier ('owner/repo' or GitHub URL).
        state: Issue state ('open', 'closed', 'all'). Defaults to 'open'.
        labels: Optional label or list of labels to filter by.
        limit: Maximum number of issues to return (1-100). Defaults to 30.
        client: Optional pre-configured GitHubClient for testing or custom auth.

    Returns:
        List of structured issue dictionaries.

    Raises:
        ValidationError: If inputs fail validation constraints.
        MCPToolExecutionError: If execution fails unexpectedly.
    """
    owner, repo_name = parse_repo_identifier(repo)

    clean_state = state.strip().lower() if isinstance(state, str) else ""
    if clean_state not in {"open", "closed", "all"}:
        raise ValidationError(
            message=f"Invalid state '{state}'. Expected 'open', 'closed', or 'all'.",
            details={"repo": repo, "state": state},
        )

    if not isinstance(limit, int) or limit < 1:
        raise ValidationError(
            message="Limit must be a positive integer.",
            details={"limit": limit},
        )

    bounded_limit = min(limit, 100)

    try:
        issues_api = GitHubIssues(client=client)
        raw_issues = await issues_api.list_issues(
            owner=owner,
            repo=repo_name,
            state=clean_state,
            labels=labels,
            per_page=bounded_limit,
            exclude_pull_requests=True,
        )

        formatted: List[Dict[str, Any]] = [
            issues_api.extract_issue_metadata(issue, repository=f"{owner}/{repo_name}")
            for issue in raw_issues
        ]
        return formatted

    except GitlexaException:
        raise
    except Exception as exc:
        logger.error("Failed to execute list_issues for %s/%s: %s", owner, repo_name, exc)
        raise MCPToolExecutionError(
            tool_name="list_issues",
            message=str(exc),
            details={"repo": repo, "state": state},
        ) from exc
