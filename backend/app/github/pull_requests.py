"""GitHub Pull Requests API wrapper for Gitlexa.

Owned by Member 03 (GitHub Integration & Repository Intelligence).
Provides structured methods to list and retrieve pull requests, inspect changed files,
evaluate review approvals and states, track branch references, assess mergeability,
extract linked issue references, and integrate CI/check status for PR investigations.
"""

from __future__ import annotations

import re
from typing import Any, AsyncIterator, Dict, List, Optional, Set

from app.core.exceptions import (
    GitHubIntegrationError,
    ResourceNotFoundError,
)
from app.core.logging import logger
from app.github.client import GitHubClient
from app.github.workflows import GitHubWorkflows


class GitHubPullRequests:
    """High-level GitHub Pull Requests API wrapper."""

    # Regex pattern to identify linked issue references in PR descriptions and commit messages
    # Matches patterns like '#123', 'fixes #123', 'closes #456', 'resolves #789'
    ISSUE_REF_PATTERN = re.compile(
        r"(?:(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+)?#(\d+)",
        re.IGNORECASE,
    )

    def __init__(
        self,
        client: Optional[GitHubClient] = None,
        workflows: Optional[GitHubWorkflows] = None,
    ) -> None:
        """Initialize with existing or new GitHubClient and GitHubWorkflows instances."""
        self.client: GitHubClient = client or GitHubClient()
        self.workflows: GitHubWorkflows = workflows or GitHubWorkflows(client=self.client)

    @classmethod
    def extract_issue_references(cls, text: Optional[str]) -> List[int]:
        """Extract referenced issue numbers from text (e.g. PR title or body).

        Args:
            text: Text content to parse.

        Returns:
            Sorted list of unique referenced issue numbers.
        """
        if not text:
            return []
        matches = cls.ISSUE_REF_PATTERN.findall(text)
        issue_numbers: Set[int] = set()
        for match in matches:
            try:
                issue_numbers.add(int(match))
            except ValueError:
                continue
        return sorted(issue_numbers)

    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        head: Optional[str] = None,
        base: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """List pull requests for a repository with optional filtering.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: PR state ('open', 'closed', 'all').
            head: Filter by head user or branch (e.g. 'user:branch-name').
            base: Filter by base branch (e.g. 'main').
            sort: Sort field ('created', 'updated', 'popularity', 'long-running').
            direction: Sort direction ('asc', 'desc').
            per_page: Results per page (max 100).
            page: Page number.

        Returns:
            List of pull request dictionaries.
        """
        params: Dict[str, Any] = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": per_page,
            "page": page,
        }
        if head:
            params["head"] = head
        if base:
            params["base"] = base

        endpoint = f"/repos/{owner}/{repo}/pulls"
        data = await self.client.get(endpoint, params=params)
        return data if isinstance(data, list) else []

    async def paginate_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        head: Optional[str] = None,
        base: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc",
        max_pages: Optional[int] = None,
        per_page: int = 30,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Asynchronously yield pull requests across paginated pages.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: PR state ('open', 'closed', 'all').
            head: Head branch filter.
            base: Base branch filter.
            sort: Sort field.
            direction: Sort direction.
            max_pages: Max pages to traverse.
            per_page: Results per page.

        Yields:
            Individual pull request dictionaries.
        """
        params: Dict[str, Any] = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": per_page,
        }
        if head:
            params["head"] = head
        if base:
            params["base"] = base

        endpoint = f"/repos/{owner}/{repo}/pulls"
        async for page_items in self.client.paginate_pages(
            endpoint, params=params, max_pages=max_pages, per_page=per_page
        ):
            for pr in page_items:
                if isinstance(pr, dict):
                    yield pr

    async def get_pull_request(
        self, owner: str, repo: str, pull_number: int
    ) -> Dict[str, Any]:
        """Retrieve full details for a single pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pull_number: Pull request number.

        Returns:
            Pull request dictionary.
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}"
        data = await self.client.get(endpoint)
        return data if isinstance(data, dict) else {}

    async def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Retrieve changed files for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pull_number: Pull request number.
            per_page: Results per page.
            page: Page number.

        Returns:
            List of changed file dictionaries with patch, additions, deletions.
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}/files"
        params = {"per_page": per_page, "page": page}
        data = await self.client.get(endpoint, params=params)
        return data if isinstance(data, list) else []

    async def get_pull_request_reviews(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Retrieve reviews submitted for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pull_number: Pull request number.
            per_page: Results per page.
            page: Page number.

        Returns:
            List of review dictionaries.
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        params = {"per_page": per_page, "page": page}
        data = await self.client.get(endpoint, params=params)
        return data if isinstance(data, list) else []

    async def get_pull_request_commits(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Retrieve commits associated with a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pull_number: Pull request number.
            per_page: Results per page.
            page: Page number.

        Returns:
            List of commit dictionaries.
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}/commits"
        params = {"per_page": per_page, "page": page}
        data = await self.client.get(endpoint, params=params)
        return data if isinstance(data, list) else []

    async def get_pull_request_details(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        include_ci: bool = True,
        include_files: bool = True,
        include_reviews: bool = True,
    ) -> Dict[str, Any]:
        """Generate unified PR intelligence summary for Evidence Engine and MCP tools.

        Aggregates PR metadata, branch references, mergeability, linked issues,
        changed files, review states, and commit CI check statuses.

        Args:
            owner: Repository owner.
            repo: Repository name.
            pull_number: Pull request number.
            include_ci: Whether to query CI check runs and commit status for head SHA.
            include_files: Whether to retrieve changed files summary.
            include_reviews: Whether to retrieve and aggregate PR reviews.

        Returns:
            Structured dictionary with comprehensive PR intelligence.
        """
        pr = await self.get_pull_request(owner, repo, pull_number)

        user_info = pr.get("user")
        author = user_info.get("login") if isinstance(user_info, dict) else None

        head = pr.get("head") if isinstance(pr.get("head"), dict) else {}
        base = pr.get("base") if isinstance(pr.get("base"), dict) else {}

        head_ref = head.get("ref")
        head_sha = head.get("sha")
        base_ref = base.get("ref")
        base_sha = base.get("sha")

        title = pr.get("title") or ""
        body = pr.get("body") or ""

        # Extract linked issue references
        linked_issues = self.extract_issue_references(f"{title}\n{body}")

        # Fetch files if requested
        files_summary: List[Dict[str, Any]] = []
        if include_files:
            raw_files = await self.get_pull_request_files(owner, repo, pull_number, per_page=100)
            for f in raw_files:
                files_summary.append({
                    "filename": f.get("filename"),
                    "status": f.get("status"),
                    "additions": f.get("additions", 0),
                    "deletions": f.get("deletions", 0),
                    "changes": f.get("changes", 0),
                })

        # Fetch and summarize reviews if requested
        review_summary: Dict[str, Any] = {
            "reviews": [],
            "approved": False,
            "changes_requested": False,
            "review_states": {},
        }
        if include_reviews:
            raw_reviews = await self.get_pull_request_reviews(owner, repo, pull_number, per_page=100)
            review_states: Dict[str, str] = {}
            for r in raw_reviews:
                reviewer = r.get("user", {}).get("login") if isinstance(r.get("user"), dict) else None
                state = r.get("state")
                if reviewer and state:
                    # Later reviews overwrite earlier reviews by same user
                    review_states[reviewer] = state

            has_approval = any(s == "APPROVED" for s in review_states.values())
            has_changes_req = any(s == "CHANGES_REQUESTED" for s in review_states.values())

            review_summary = {
                "reviews": raw_reviews,
                "approved": has_approval,
                "changes_requested": has_changes_req,
                "review_states": review_states,
            }

        # Fetch CI checks if requested and head_sha is known
        ci_summary: Dict[str, Any] = {
            "head_sha": head_sha,
            "check_runs": [],
            "combined_status": None,
            "has_ci_failures": False,
        }
        if include_ci and head_sha:
            try:
                check_runs = await self.workflows.get_commit_check_runs(owner, repo, head_sha)
                combined_status = await self.workflows.get_commit_status(owner, repo, head_sha)

                failing_conclusions = self.workflows.FAILED_CONCLUSIONS
                has_check_failure = any(
                    str(c.get("conclusion") or "").lower() in failing_conclusions
                    for c in check_runs
                )
                has_status_failure = str(combined_status.get("state") or "").lower() in {"failure", "error"}

                ci_summary = {
                    "head_sha": head_sha,
                    "check_runs": check_runs,
                    "combined_status": combined_status,
                    "has_ci_failures": has_check_failure or has_status_failure,
                }
            except Exception as exc:
                logger.debug("Failed to retrieve CI checks for PR %d head SHA %s: %s", pull_number, head_sha, exc)

        return {
            "id": pr.get("id"),
            "number": pr.get("number"),
            "title": title,
            "state": pr.get("state") or "open",
            "draft": pr.get("draft", False),
            "merged": pr.get("merged", False),
            "merged_at": pr.get("merged_at"),
            "mergeable": pr.get("mergeable"),
            "mergeable_state": pr.get("mergeable_state"),
            "author": author,
            "user": author,
            "head_ref": head_ref,
            "head_sha": head_sha,
            "base_ref": base_ref,
            "base_sha": base_sha,
            "html_url": pr.get("html_url"),
            "body": body,
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "closed_at": pr.get("closed_at"),
            "linked_issues": linked_issues,
            "changed_files_count": pr.get("changed_files", len(files_summary)),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "files": files_summary,
            "review": review_summary,
            "ci": ci_summary,
            "repository": f"{owner}/{repo}",
        }
