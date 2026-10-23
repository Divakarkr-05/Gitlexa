"""GitHub Code Search API wrapper for Gitlexa.

Owned by Member 03 (GitHub Integration & Repository Intelligence).
Provides structured methods to search repository source code, handle GitHub
search query qualifiers and pagination limits, extract text matches and snippets,
and provide normalized code findings for the Evidence Engine and MCP tools.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional

from app.core.exceptions import (
    AuthenticationError,
    GitHubIntegrationError,
    RateLimitExceededError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.logging import logger
from app.github.client import GitHubClient


class GitHubCodeSearch:
    """High-level GitHub Code Search API wrapper."""

    # GitHub Search API headers to request text match snippets
    TEXT_MATCH_ACCEPT = "application/vnd.github.text-match+json"

    def __init__(self, client: Optional[GitHubClient] = None) -> None:
        """Initialize with an existing or new GitHubClient instance."""
        self.client: GitHubClient = client or GitHubClient()

    @staticmethod
    def build_search_query(
        query: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        path: Optional[str] = None,
        extension: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:
        """Construct a GitHub code search query string with supported qualifiers.

        Args:
            query: Free-text search term or regex/token.
            owner: Optional repository owner (used with repo).
            repo: Optional repository name.
            path: Optional file directory path (e.g. 'backend/app').
            extension: Optional file extension filter (e.g. 'py' or '.py').
            filename: Optional filename filter (e.g. 'Dockerfile').

        Returns:
            Assembled query string with qualifiers.
        """
        parts: List[str] = []
        clean_query = query.strip()
        if clean_query:
            parts.append(clean_query)

        # Scoping to repository: 'repo:owner/repo'
        if owner and repo:
            repo_qualifier = f"repo:{owner}/{repo}"
            if repo_qualifier not in clean_query:
                parts.append(repo_qualifier)
        elif repo and "/" in repo:
            repo_qualifier = f"repo:{repo}"
            if repo_qualifier not in clean_query:
                parts.append(repo_qualifier)

        # Path qualifier: 'path:directory'
        if path:
            clean_path = path.strip().lstrip("/")
            path_qualifier = f"path:{clean_path}"
            if path_qualifier not in clean_query:
                parts.append(path_qualifier)

        # Extension qualifier: 'extension:py'
        if extension:
            clean_ext = extension.strip().lstrip(".")
            ext_qualifier = f"extension:{clean_ext}"
            if ext_qualifier not in clean_query:
                parts.append(ext_qualifier)

        # Filename qualifier: 'filename:name'
        if filename:
            clean_fn = filename.strip()
            fn_qualifier = f"filename:{clean_fn}"
            if fn_qualifier not in clean_query:
                parts.append(fn_qualifier)

        return " ".join(parts)

    @staticmethod
    def extract_code_match_details(item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured match details from a raw code search item.

        Parses GitHub's text_matches structures into readable snippet blocks.
        """
        snippets: List[str] = []
        text_matches = item.get("text_matches", [])

        if isinstance(text_matches, list):
            for match in text_matches:
                if isinstance(match, dict) and "fragment" in match:
                    fragment = match.get("fragment")
                    if fragment and fragment not in snippets:
                        snippets.append(fragment)

        repo_info = item.get("repository") if isinstance(item.get("repository"), dict) else {}
        repo_name = repo_info.get("full_name") or repo_info.get("name")

        return {
            "name": item.get("name"),
            "path": item.get("path"),
            "sha": item.get("sha"),
            "html_url": item.get("html_url"),
            "repository": repo_name,
            "snippets": snippets,
            "text_matches": text_matches,
        }

    async def search_code(
        self,
        query: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        path: Optional[str] = None,
        extension: Optional[str] = None,
        filename: Optional[str] = None,
        sort: Optional[str] = None,
        order: str = "desc",
        per_page: int = 30,
        page: int = 1,
        include_text_matches: bool = True,
    ) -> Dict[str, Any]:
        """Search code across GitHub with optional repository and qualifier filters.

        Args:
            query: Free-text query string.
            owner: Optional repository owner.
            repo: Optional repository name.
            path: Optional directory filter.
            extension: Optional file extension filter.
            filename: Optional filename filter.
            sort: Sort field (e.g. 'indexed'). Leave None for best match.
            order: Sort direction ('asc', 'desc').
            per_page: Results per page (max 100).
            page: Page number (max 10 allowed by GitHub search API).
            include_text_matches: Whether to request text match fragments.

        Returns:
            Dictionary with 'total_count', 'incomplete_results', and 'items'.
        """
        full_query = self.build_search_query(
            query=query,
            owner=owner,
            repo=repo,
            path=path,
            extension=extension,
            filename=filename,
        )

        if not full_query.strip():
            raise ValidationError(
                message="Code search query cannot be empty.",
                details={"query": query},
            )

        params: Dict[str, Any] = {
            "q": full_query,
            "per_page": min(per_page, 100),
            "page": page,
        }
        if sort:
            params["sort"] = sort
            params["order"] = order

        headers = {"Accept": self.TEXT_MATCH_ACCEPT} if include_text_matches else None
        endpoint = "/search/code"

        try:
            data = await self.client.get(endpoint, params=params, headers=headers)
        except GitHubIntegrationError as exc:
            # Check for GitHub unprocessable entity (422) on search queries
            if exc.status_code == 422:
                raise ValidationError(
                    message=f"Invalid GitHub code search query: {exc.message}",
                    details={"query": full_query, **exc.details},
                ) from exc
            raise

        if isinstance(data, dict):
            return {
                "total_count": data.get("total_count", 0),
                "incomplete_results": data.get("incomplete_results", False),
                "items": data.get("items", []),
                "query": full_query,
            }

        return {"total_count": 0, "incomplete_results": False, "items": [], "query": full_query}

    async def paginate_code_search(
        self,
        query: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        path: Optional[str] = None,
        extension: Optional[str] = None,
        filename: Optional[str] = None,
        max_pages: Optional[int] = None,
        per_page: int = 30,
        include_text_matches: bool = True,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Asynchronously yield code search match items across pages.

        Note: GitHub Search API limits pagination to at most 1,000 total results (typically 10 pages).

        Args:
            query: Query string.
            owner: Repository owner.
            repo: Repository name.
            path: Directory path filter.
            extension: File extension filter.
            filename: Filename filter.
            max_pages: Max pages to traverse.
            per_page: Items per page.
            include_text_matches: Request text matches.

        Yields:
            Individual code match dictionaries.
        """
        full_query = self.build_search_query(
            query=query,
            owner=owner,
            repo=repo,
            path=path,
            extension=extension,
            filename=filename,
        )

        params = {"q": full_query, "per_page": min(per_page, 100)}
        headers = {"Accept": self.TEXT_MATCH_ACCEPT} if include_text_matches else None
        endpoint = "/search/code"

        async for page_items in self.client.paginate_pages(
            endpoint, params=params, headers=headers, max_pages=max_pages, per_page=per_page
        ):
            for item in page_items:
                if isinstance(item, dict):
                    yield item

    async def search_repository_code(
        self,
        owner: str,
        repo: str,
        query: str,
        path: Optional[str] = None,
        extension: Optional[str] = None,
        filename: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Search code within a specific repository and return normalized matches.

        Provides structured findings compatible with the Evidence Engine and MCP tools.

        Args:
            owner: Repository owner.
            repo: Repository name.
            query: Search term or pattern.
            path: Optional directory filter.
            extension: Optional file extension filter.
            filename: Optional filename filter.
            per_page: Results per page.
            page: Page number.

        Returns:
            List of normalized code match dictionaries containing snippet extracts.
        """
        result = await self.search_code(
            query=query,
            owner=owner,
            repo=repo,
            path=path,
            extension=extension,
            filename=filename,
            per_page=per_page,
            page=page,
            include_text_matches=True,
        )

        raw_items = result.get("items", [])
        formatted_matches: List[Dict[str, Any]] = []

        for item in raw_items:
            match = self.extract_code_match_details(item)
            if not match["repository"]:
                match["repository"] = f"{owner}/{repo}"
            formatted_matches.append(match)

        return formatted_matches
