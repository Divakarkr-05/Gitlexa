"""GitHub Issues API wrapper for Gitlexa.

Owned by Member 03 (GitHub Integration & Repository Intelligence).
Provides structured methods to list issues, filter by state/labels/assignee,
retrieve individual issues, extract issue comments, distinguish pull requests
from ordinary issues, and produce normalized issue metadata for the
Evidence Engine and MCP tools.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional, Union

from app.core.exceptions import (
    GitHubIntegrationError,
    ResourceNotFoundError,
)
from app.core.logging import logger
from app.github.client import GitHubClient


class GitHubIssues:
    """High-level GitHub Issues API wrapper."""

    def __init__(self, client: Optional[GitHubClient] = None) -> None:
        """Initialize with an existing or new GitHubClient instance."""
        self.client: GitHubClient = client or GitHubClient()

    @staticmethod
    def is_pull_request(issue_data: Dict[str, Any]) -> bool:
        """Determine whether an issue payload returned by GitHub is a Pull Request.

        GitHub's `/repos/{owner}/{repo}/issues` endpoint returns both Issues and
        Pull Requests. PRs include a 'pull_request' key with links.
        """
        return bool(issue_data.get("pull_request"))

    @staticmethod
    def extract_issue_metadata(
        issue: Dict[str, Any], repository: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured, normalized metadata from raw GitHub issue payload.

        Returns a dictionary compatible with the Evidence Engine and MCP tools.
        """
        user_info = issue.get("user")
        author = user_info.get("login") if isinstance(user_info, dict) else None

        raw_labels = issue.get("labels", [])
        labels = [
            label.get("name") if isinstance(label, dict) else str(label)
            for label in raw_labels
            if label
        ]

        raw_assignees = issue.get("assignees", [])
        assignees = [
            assignee.get("login") if isinstance(assignee, dict) else str(assignee)
            for assignee in raw_assignees
            if assignee
        ]

        assignee_info = issue.get("assignee")
        primary_assignee = (
            assignee_info.get("login") if isinstance(assignee_info, dict) else None
        )

        milestone_info = issue.get("milestone")
        milestone = (
            milestone_info.get("title") if isinstance(milestone_info, dict) else None
        )

        is_pr = GitHubIssues.is_pull_request(issue)

        return {
            "id": issue.get("id"),
            "number": issue.get("number"),
            "title": issue.get("title") or "",
            "state": issue.get("state") or "open",
            "state_reason": issue.get("state_reason"),
            "body": issue.get("body") or "",
            "author": author,
            "user": author,
            "labels": labels,
            "assignee": primary_assignee,
            "assignees": assignees,
            "milestone": milestone,
            "comments_count": issue.get("comments", 0),
            "is_pull_request": is_pr,
            "html_url": issue.get("html_url"),
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "closed_at": issue.get("closed_at"),
            "repository": repository,
        }

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[Union[str, List[str]]] = None,
        assignee: Optional[str] = None,
        creator: Optional[str] = None,
        mentioned: Optional[str] = None,
        milestone: Optional[Union[str, int]] = None,
        sort: str = "created",
        direction: str = "desc",
        since: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
        exclude_pull_requests: bool = True,
    ) -> List[Dict[str, Any]]:
        """List issues for a repository with optional filtering.

        Args:
            owner: Repository owner or organization.
            repo: Repository name.
            state: Issue state ('open', 'closed', 'all').
            labels: Single label string or list of label names.
            assignee: Filter by assigned GitHub username (or 'none' / '*').
            creator: Filter by creator username.
            mentioned: Filter by mentioned username.
            milestone: Milestone number or title (or 'none' / '*').
            sort: Sort field ('created', 'updated', 'comments').
            direction: Sort direction ('asc', 'desc').
            since: ISO 8601 timestamp string (e.g. '2026-01-01T00:00:00Z').
            per_page: Number of items per page (max 100).
            page: Page number to fetch.
            exclude_pull_requests: When True, filters out PR items returned by GitHub.

        Returns:
            List of raw or filtered issue dictionaries.
        """
        params: Dict[str, Any] = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": per_page,
            "page": page,
        }

        if labels:
            params["labels"] = ",".join(labels) if isinstance(labels, list) else labels
        if assignee:
            params["assignee"] = assignee
        if creator:
            params["creator"] = creator
        if mentioned:
            params["mentioned"] = mentioned
        if milestone is not None:
            params["milestone"] = milestone
        if since:
            params["since"] = since

        endpoint = f"/repos/{owner}/{repo}/issues"
        data = await self.client.get(endpoint, params=params)

        if not isinstance(data, list):
            return []

        if exclude_pull_requests:
            return [issue for issue in data if not self.is_pull_request(issue)]
        return data

    async def paginate_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[Union[str, List[str]]] = None,
        assignee: Optional[str] = None,
        creator: Optional[str] = None,
        mentioned: Optional[str] = None,
        milestone: Optional[Union[str, int]] = None,
        sort: str = "created",
        direction: str = "desc",
        since: Optional[str] = None,
        max_pages: Optional[int] = None,
        per_page: int = 30,
        exclude_pull_requests: bool = True,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Asynchronously yield issues across paginated results.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Issue state ('open', 'closed', 'all').
            labels: Filter by labels.
            assignee: Filter by assignee.
            creator: Filter by creator.
            mentioned: Filter by mentioned user.
            milestone: Filter by milestone.
            sort: Sort field.
            direction: Sort direction.
            since: ISO timestamp filter.
            max_pages: Maximum pages to fetch.
            per_page: Number of items per page.
            exclude_pull_requests: Whether to omit pull requests from results.

        Yields:
            Individual issue dictionaries.
        """
        params: Dict[str, Any] = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": per_page,
        }

        if labels:
            params["labels"] = ",".join(labels) if isinstance(labels, list) else labels
        if assignee:
            params["assignee"] = assignee
        if creator:
            params["creator"] = creator
        if mentioned:
            params["mentioned"] = mentioned
        if milestone is not None:
            params["milestone"] = milestone
        if since:
            params["since"] = since

        endpoint = f"/repos/{owner}/{repo}/issues"
        async for page_items in self.client.paginate_pages(
            endpoint, params=params, max_pages=max_pages, per_page=per_page
        ):
            for item in page_items:
                if isinstance(item, dict):
                    if exclude_pull_requests and self.is_pull_request(item):
                        continue
                    yield item

    async def get_issue(
        self, owner: str, repo: str, issue_number: int
    ) -> Dict[str, Any]:
        """Retrieve details for a single issue.

        Args:
            owner: Repository owner.
            repo: Repository name.
            issue_number: Issue number.

        Returns:
            Issue dictionary.
        """
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}"
        data = await self.client.get(endpoint)
        return data if isinstance(data, dict) else {}

    async def get_issue_comments(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Retrieve comments for a specific issue.

        Args:
            owner: Repository owner.
            repo: Repository name.
            issue_number: Issue number.
            per_page: Number of comments per page.
            page: Page number.

        Returns:
            List of issue comment dictionaries.
        """
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        params = {"per_page": per_page, "page": page}
        data = await self.client.get(endpoint, params=params)
        return data if isinstance(data, list) else []

    async def get_issue_summary(
        self, owner: str, repo: str, issue_number: int
    ) -> Dict[str, Any]:
        """Retrieve and format structured issue intelligence.

        Args:
            owner: Repository owner.
            repo: Repository name.
            issue_number: Issue number.

        Returns:
            Normalized dictionary with issue metadata.
        """
        raw_issue = await self.get_issue(owner, repo, issue_number)
        return self.extract_issue_metadata(
            raw_issue, repository=f"{owner}/{repo}"
        )
