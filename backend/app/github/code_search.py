"""GitHub Code Search API wrapper.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Searches repository source code with filters and text snippets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.github.client import GitHubClient


class GitHubCodeSearch:
    """Wrapper for GitHub Code Search REST API."""

    def __init__(self, client: Optional[GitHubClient] = None) -> None:
        self.client = client or GitHubClient()

    async def search_repository_code(
        self,
        owner: str,
        repo: str,
        query: str,
        path: Optional[str] = None,
        extension: Optional[str] = None,
        filename: Optional[str] = None,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """Search code within a GitHub repository."""
        q_parts = [f"repo:{owner}/{repo}", query]
        if path:
            q_parts.append(f"path:{path}")
        if extension:
            clean_ext = extension.lstrip(".")
            q_parts.append(f"extension:{clean_ext}")
        if filename:
            q_parts.append(f"filename:{filename}")

        params: Dict[str, Any] = {
            "q": " ".join(q_parts),
            "per_page": per_page,
        }
        headers = {"Accept": "application/vnd.github.v3.text-match+json"}

        response = await self.client.get("/search/code", params=params, headers=headers)
        data = response.json()
        items = data.get("items", []) if isinstance(data, dict) else []
        if not isinstance(items, list):
            return []

        results: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            snippets: List[str] = []
            raw_text_matches = item.get("text_matches", [])
            if isinstance(raw_text_matches, list):
                for tm in raw_text_matches:
                    if isinstance(tm, dict):
                        frag = tm.get("fragment")
                        if isinstance(frag, str):
                            snippets.append(frag)

            repo_val = (
                item.get("repository", {}).get("full_name")
                if isinstance(item.get("repository"), dict)
                else f"{owner}/{repo}"
            )

            results.append(
                {
                    "name": item.get("name", ""),
                    "path": item.get("path", ""),
                    "sha": item.get("sha", ""),
                    "html_url": item.get("html_url", ""),
                    "repository": repo_val,
                    "snippets": snippets,
                }
            )

        return results
