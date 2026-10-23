"""MCP Tool: search_code.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Searches repository source code for patterns, identifiers, and error strings,
returning matching file paths and code snippets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.exceptions import (
    GitlexaException,
    MCPToolExecutionError,
    ValidationError,
)
from app.core.logging import logger
from app.github.client import GitHubClient
from app.github.code_search import GitHubCodeSearch
from app.mcp.tools.list_issues import parse_repo_identifier


async def search_code(
    repo: str,
    query: str,
    path: Optional[str] = None,
    extension: Optional[str] = None,
    filename: Optional[str] = None,
    limit: int = 30,
    client: Optional[GitHubClient] = None,
) -> List[Dict[str, Any]]:
    """MCP tool to search repository source code.

    Args:
        repo: Repository identifier ('owner/repo' or GitHub URL).
        query: Search term or pattern.
        path: Optional directory path filter.
        extension: Optional file extension filter.
        filename: Optional filename filter.
        limit: Maximum number of matches to return (1-100). Defaults to 30.
        client: Optional pre-configured GitHubClient for testing or custom auth.

    Returns:
        List of structured code match dictionaries with snippets.

    Raises:
        ValidationError: If inputs fail validation constraints.
        AuthenticationError: If search is attempted without authentication.
        MCPToolExecutionError: If execution fails unexpectedly.
    """
    owner, repo_name = parse_repo_identifier(repo)

    if not query or not isinstance(query, str) or not query.strip():
        raise ValidationError(
            message="Search query cannot be empty.",
            details={"repo": repo, "query": query},
        )

    if not isinstance(limit, int) or limit < 1:
        raise ValidationError(
            message="Limit must be a positive integer.",
            details={"limit": limit},
        )

    bounded_limit = min(limit, 100)

    try:
        search_api = GitHubCodeSearch(client=client)
        matches = await search_api.search_repository_code(
            owner=owner,
            repo=repo_name,
            query=query.strip(),
            path=path,
            extension=extension,
            filename=filename,
            per_page=bounded_limit,
        )
        return matches

    except GitlexaException:
        raise
    except Exception as exc:
        logger.error("Failed to execute search_code for %s/%s query '%s': %s", owner, repo_name, query, exc)
        raise MCPToolExecutionError(
            tool_name="search_code",
            message=str(exc),
            details={"repo": repo, "query": query},
        ) from exc
