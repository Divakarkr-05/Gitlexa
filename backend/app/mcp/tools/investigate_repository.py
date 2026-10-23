"""MCP Tool: investigate_repository.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Collects comprehensive repository telemetry (metadata, issues, PRs, commits, CI runs)
using existing GitHub wrappers and normalizes them into structured evidence.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.core.exceptions import (
    GitlexaException,
    MCPToolExecutionError,
    ValidationError,
)
from app.core.logging import logger
from app.evidence.github_adapter import GitHubEvidenceAdapter
from app.github.client import GitHubClient
from app.github.commits import GitHubCommits
from app.github.issues import GitHubIssues
from app.github.pull_requests import GitHubPullRequests
from app.github.workflows import GitHubWorkflows
from app.mcp.tools.list_issues import parse_repo_identifier


def resolve_owner_repo(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
) -> Tuple[str, str]:
    """Resolve and validate owner and repo arguments from various input formats."""
    if repo and "/" in repo:
        return parse_repo_identifier(repo)

    if not owner or not str(owner).strip():
        raise ValidationError(
            message="Repository owner must be specified.",
            details={"owner": owner, "repo": repo},
        )
    if not repo or not str(repo).strip():
        raise ValidationError(
            message="Repository name must be specified.",
            details={"owner": owner, "repo": repo},
        )

    return owner.strip(), repo.strip()


async def investigate_repository(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    client: Optional[GitHubClient] = None,
    max_items: int = 10,
) -> Dict[str, Any]:
    """Investigate a repository and extract actual issues, PRs, commits, and CI runs.

    Args:
        owner: Repository owner/org (e.g. 'Divakarkr-05').
        repo: Repository name (e.g. 'Gitlexa' or 'Divakarkr-05/Gitlexa').
        client: Optional pre-configured GitHubClient.
        max_items: Maximum items to collect per telemetry type (default 10).

    Returns:
        Structured dictionary with repository information, issues, PRs, commits,
        CI status, and evidence count.
    """
    clean_owner, clean_repo = resolve_owner_repo(owner=owner, repo=repo)
    full_repo_name = f"{clean_owner}/{clean_repo}"
    active_client = client or GitHubClient()

    try:
        issues_api = GitHubIssues(client=active_client)
        prs_api = GitHubPullRequests(client=active_client)
        workflows_api = GitHubWorkflows(client=active_client)
        commits_api = GitHubCommits(client=active_client)

        # 1. Fetch recent issues
        raw_issues: List[Dict[str, Any]] = []
        try:
            raw_issues = await issues_api.list_issues(
                owner=clean_owner,
                repo=clean_repo,
                state="all",
                per_page=max_items,
                exclude_pull_requests=True,
            )
        except Exception as exc:
            logger.warning("Could not fetch issues for %s: %s", full_repo_name, exc)

        # 2. Fetch recent pull requests
        raw_prs: List[Dict[str, Any]] = []
        try:
            raw_prs = await prs_api.list_pull_requests(
                owner=clean_owner,
                repo=clean_repo,
                state="all",
                per_page=max_items,
            )
        except Exception as exc:
            logger.warning("Could not fetch PRs for %s: %s", full_repo_name, exc)

        # 3. Fetch recent commits
        raw_commits: List[Dict[str, Any]] = []
        try:
            raw_commits = await commits_api.list_commits(
                owner=clean_owner,
                repo=clean_repo,
                per_page=max_items,
            )
        except Exception as exc:
            logger.warning("Could not fetch commits for %s: %s", full_repo_name, exc)

        # 4. Fetch CI workflow status
        ci_summary: List[Dict[str, Any]] = []
        try:
            summary = await workflows_api.get_ci_summary(
                owner=clean_owner,
                repo=clean_repo,
            )
            if summary.get("run_id") is not None:
                ci_summary.append(summary)
            else:
                runs = await workflows_api.list_workflow_runs(
                    owner=clean_owner,
                    repo=clean_repo,
                    per_page=max_items,
                )
                ci_summary = runs
        except Exception as exc:
            logger.warning("Could not fetch CI runs for %s: %s", full_repo_name, exc)

        # 5. Build Evidence Bundle using existing Evidence Engine adapter
        adapter = GitHubEvidenceAdapter()
        bundle = adapter.collect(
            repository=full_repo_name,
            issues=raw_issues,
            pull_requests=raw_prs,
            ci_runs=ci_summary,
            commits=raw_commits,
        )

        return {
            "repository": full_repo_name,
            "issues": raw_issues,
            "pull_requests": raw_prs,
            "commits": raw_commits,
            "ci_status": ci_summary,
            "evidence_count": len(bundle.evidence),
        }

    except GitlexaException:
        raise
    except Exception as exc:
        logger.error("Failed to investigate repository %s: %s", full_repo_name, exc)
        raise MCPToolExecutionError(
            tool_name="investigate_repository",
            message=str(exc),
            details={"repository": full_repo_name},
        ) from exc
