"""GitHub Commits API wrapper.

Owned by Member 03 (GitHub Integration & Repository Intelligence).
Fetches and formats GitHub repository commits.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.github.client import GitHubClient


class GitHubCommits:
    """Wrapper for GitHub Commits REST API."""

    def __init__(self, client: Optional[GitHubClient] = None) -> None:
        self.client: GitHubClient = client or GitHubClient()

    async def list_commits(
        self,
        owner: str,
        repo: str,
        sha: Optional[str] = None,
        path: Optional[str] = None,
        author: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """List repository commits with optional filtering."""
        params: Dict[str, Any] = {"per_page": per_page, "page": page}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        if author:
            params["author"] = author

        endpoint = f"/repos/{owner}/{repo}/commits"
        data = await self.client.get(endpoint, params=params)
        return data if isinstance(data, list) else []
