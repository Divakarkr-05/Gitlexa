"""GitHub Issues API wrapper.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Fetches and formats GitHub repository issues.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from app.github.client import GitHubClient


class GitHubIssues:
    """Wrapper for GitHub Issues REST API."""

    def __init__(self, client: Optional[GitHubClient] = None) -> None:
        self.client = client or GitHubClient()

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        labels: Optional[Union[List[str], str]] = None,
        per_page: int = 30,
        exclude_pull_requests: bool = True,
    ) -> List[Dict[str, Any]]:
        """List issues for a repository."""
        params: Dict[str, Any] = {
            "state": state,
            "per_page": per_page,
        }
        if labels:
            if isinstance(labels, list):
                params["labels"] = ",".join(labels)
            else:
                params["labels"] = labels

        endpoint = f"/repos/{owner}/{repo}/issues"
        response = await self.client.get(endpoint, params=params)
        data = response.json()
        if not isinstance(data, list):
            return []

        if exclude_pull_requests:
            return [issue for issue in data if isinstance(issue, dict) and "pull_request" not in issue]
        return [issue for issue in data if isinstance(issue, dict)]

    def extract_issue_metadata(
        self,
        issue: Dict[str, Any],
        repository: str = "",
    ) -> Dict[str, Any]:
        """Normalize an issue payload into a structured dictionary."""
        user = issue.get("user")
        author = user.get("login") if isinstance(user, dict) else None

        raw_labels = issue.get("labels", [])
        labels: List[str] = []
        if isinstance(raw_labels, list):
            for lbl in raw_labels:
                if isinstance(lbl, dict) and "name" in lbl:
                    labels.append(str(lbl["name"]))
                elif isinstance(lbl, str):
                    labels.append(lbl)

        repo_name = repository or (
            issue.get("repository", {}).get("full_name")
            if isinstance(issue.get("repository"), dict)
            else ""
        )

        return {
            "id": issue.get("id"),
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "author": author,
            "repository": repo_name,
            "state": issue.get("state", ""),
            "body": issue.get("body", "") or "",
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "html_url": issue.get("html_url", ""),
            "labels": labels,
            "comments_count": issue.get("comments", 0),
        }
