"""GitHub Pull Requests API wrapper.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Fetches and formats GitHub pull request details, files, reviews, and CI status.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.exceptions import ResourceNotFoundError
from app.github.client import GitHubClient


class GitHubPullRequests:
    """Wrapper for GitHub Pull Requests REST API."""

    def __init__(self, client: Optional[GitHubClient] = None) -> None:
        self.client = client or GitHubClient()

    async def get_pull_request_details(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        include_ci: bool = True,
        include_files: bool = True,
        include_reviews: bool = True,
    ) -> Dict[str, Any]:
        """Fetch full details for a pull request."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pull_number}"
        try:
            response = await self.client.get(endpoint)
            pr_data = response.json()
        except ResourceNotFoundError:
            raise ResourceNotFoundError(
                resource_name="Pull Request",
                identifier=f"{owner}/{repo}#{pull_number}",
            )

        head = pr_data.get("head") if isinstance(pr_data.get("head"), dict) else {}
        head_ref = head.get("ref", "")
        head_sha = head.get("sha", "")
        base = pr_data.get("base") if isinstance(pr_data.get("base"), dict) else {}
        base_ref = base.get("ref", "")

        user = pr_data.get("user")
        author = user.get("login") if isinstance(user, dict) else None

        files: List[Dict[str, Any]] = []
        if include_files:
            try:
                files_resp = await self.client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}/files")
                files_data = files_resp.json()
                if isinstance(files_data, list):
                    files = files_data
            except Exception:
                files = []

        review_summary: Dict[str, Any] = {"approved": False, "reviews": []}
        if include_reviews:
            try:
                reviews_resp = await self.client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews")
                reviews_data = reviews_resp.json()
                if isinstance(reviews_data, list):
                    approved = any(
                        isinstance(r, dict) and r.get("state") == "APPROVED"
                        for r in reviews_data
                    )
                    review_summary = {"approved": approved, "reviews": reviews_data}
            except Exception:
                pass

        ci_data: Dict[str, Any] = {}
        if include_ci and head_sha:
            try:
                ci_resp = await self.client.get(f"/repos/{owner}/{repo}/commits/{head_sha}/check-runs")
                ci_data = ci_resp.json() if isinstance(ci_resp.json(), dict) else {}
            except Exception:
                ci_data = {}

        return {
            "id": pr_data.get("id"),
            "number": pr_data.get("number"),
            "title": pr_data.get("title", ""),
            "state": pr_data.get("state", ""),
            "body": pr_data.get("body", "") or "",
            "author": author,
            "head_ref": head_ref,
            "head_sha": head_sha,
            "base_ref": base_ref,
            "mergeable": pr_data.get("mergeable"),
            "mergeable_state": pr_data.get("mergeable_state"),
            "created_at": pr_data.get("created_at"),
            "updated_at": pr_data.get("updated_at"),
            "html_url": pr_data.get("html_url", ""),
            "files": files,
            "review": review_summary,
            "ci": ci_data,
        }
