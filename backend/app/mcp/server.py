"""MCP Server implementation for Gitlexa.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Provides tool registration, discovery, parameter validation, and asynchronous
execution for the Model Context Protocol (MCP) server.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional

from app.core.exceptions import (
    GitlexaException,
    MCPToolExecutionError,
)
from app.core.logging import logger
from app.github.client import GitHubClient
from app.mcp.tools.get_blocker_diagnosis import get_blocker_diagnosis
from app.mcp.tools.get_project_status import get_project_status
from app.mcp.tools.get_pull_request import get_pull_request
from app.mcp.tools.get_recovery_plan import get_recovery_plan
from app.mcp.tools.investigate_repository import investigate_repository
from app.mcp.tools.list_issues import list_issues
from app.mcp.tools.read_ci_status import read_ci_status
from app.mcp.tools.search_code import search_code


class MCPServer:
    """Model Context Protocol (MCP) tool registry and execution server."""

    def __init__(self) -> None:
        """Initialize empty tool registry and metadata cache."""
        self.tools: Dict[str, Callable[..., Any]] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        func: Callable[..., Any],
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a tool with the MCP server.

        Args:
            name: Tool name identifier (e.g. 'list_issues').
            func: Synchronous or asynchronous callable implementing the tool.
            description: Optional human-readable description of the tool.
            parameters: Optional parameter schema description.
        """
        self.tools[name] = func
        self.tool_metadata[name] = {
            "name": name,
            "description": description or func.__doc__ or "",
            "parameters": parameters or {},
        }
        logger.debug("Registered MCP tool: %s", name)

    def get_tool(self, name: str) -> Optional[Callable[..., Any]]:
        """Retrieve registered tool callable by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with their metadata schemas."""
        return list(self.tool_metadata.values())

    async def execute_tool(self, name: str, **arguments: Any) -> Any:
        """Execute a registered tool by name with keyword arguments.

        Args:
            name: Name of the tool to execute.
            **arguments: Keyword arguments passed directly to the tool callable.

        Returns:
            The structured result of the tool invocation.

        Raises:
            MCPToolExecutionError: If tool is not registered or fails execution.
            GitlexaException: If domain validation or integration error occurs.
        """
        tool = self.get_tool(name)
        if tool is None:
            raise MCPToolExecutionError(
                tool_name=name,
                message=f"Tool '{name}' is not registered on this MCP server.",
                details={"available_tools": list(self.tools.keys())},
            )

        logger.debug("Executing MCP tool '%s' with arguments: %s", name, arguments)

        try:
            if inspect.iscoroutinefunction(tool):
                return await tool(**arguments)
            elif callable(tool):
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, lambda: tool(**arguments))
            else:
                raise MCPToolExecutionError(
                    tool_name=name,
                    message=f"Registered tool '{name}' is not callable.",
                )
        except GitlexaException:
            raise
        except Exception as exc:
            logger.error("Unhandled error executing MCP tool '%s': %s", name, exc)
            raise MCPToolExecutionError(
                tool_name=name,
                message=str(exc),
                details={"arguments": arguments},
            ) from exc

    async def invoke_tool(
        self, tool_name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Invoke a tool with a dictionary of arguments.

        Aligns with AlexaMCPClient and Agent invocation interfaces.
        """
        args = arguments or {}
        return await self.execute_tool(tool_name, **args)


def create_mcp_server(client: Optional[GitHubClient] = None) -> MCPServer:
    """Factory to create an MCPServer pre-registered with read-only GitHub tools.

    Args:
        client: Optional pre-configured GitHubClient instance (e.g. for testing).

    Returns:
        Configured MCPServer instance.
    """
    server = MCPServer()

    async def _list_issues(**kw: Any) -> Any:
        if "client" not in kw and client is not None:
            kw["client"] = client
        return await list_issues(**kw)

    async def _get_pull_request(**kw: Any) -> Any:
        if "client" not in kw and client is not None:
            kw["client"] = client
        return await get_pull_request(**kw)

    async def _read_ci_status(**kw: Any) -> Any:
        if "client" not in kw and client is not None:
            kw["client"] = client
        return await read_ci_status(**kw)

    async def _search_code(**kw: Any) -> Any:
        if "client" not in kw and client is not None:
            kw["client"] = client
        return await search_code(**kw)

    async def _investigate_repository(**kw: Any) -> Any:
        if "client" not in kw and client is not None:
            kw["client"] = client
        return await investigate_repository(**kw)

    async def _get_project_status(**kw: Any) -> Any:
        if "client" not in kw and client is not None:
            kw["client"] = client
        return await get_project_status(**kw)

    async def _get_blocker_diagnosis(**kw: Any) -> Any:
        if "client" not in kw and client is not None:
            kw["client"] = client
        return await get_blocker_diagnosis(**kw)

    async def _get_recovery_plan(**kw: Any) -> Any:
        if "client" not in kw and client is not None:
            kw["client"] = client
        return await get_recovery_plan(**kw)

    server.register_tool(
        name="list_issues",
        func=_list_issues,
        description="Retrieves open/closed issues with label filters for a repository.",
        parameters={
            "repo": "str (required): 'owner/repo' or GitHub repository URL",
            "state": "str (optional): 'open', 'closed', or 'all'",
            "labels": "list[str] or str (optional): label filters",
            "limit": "int (optional): max issues to return (1-100)",
        },
    )

    server.register_tool(
        name="get_pull_request",
        func=_get_pull_request,
        description="Retrieves PR status, review states, diff summary, and CI status.",
        parameters={
            "repo": "str (required): 'owner/repo' or GitHub repository URL",
            "pr_number": "int (required): pull request number",
            "include_ci": "bool (optional): whether to query CI checks",
            "include_files": "bool (optional): whether to include changed files",
            "include_reviews": "bool (optional): whether to include reviews",
        },
    )

    server.register_tool(
        name="read_ci_status",
        func=_read_ci_status,
        description="Returns latest GitHub Actions workflow run statuses for a repository branch.",
        parameters={
            "repo": "str (required): 'owner/repo' or GitHub repository URL",
            "branch": "str (optional): branch name (e.g. 'main')",
            "sha": "str (optional): commit SHA",
        },
    )

    server.register_tool(
        name="search_code",
        func=_search_code,
        description="Searches repository source code for patterns and returns snippets.",
        parameters={
            "repo": "str (required): 'owner/repo' or GitHub repository URL",
            "query": "str (required): search pattern or identifier",
            "path": "str (optional): directory filter",
            "extension": "str (optional): file extension filter",
            "filename": "str (optional): filename filter",
            "limit": "int (optional): max results (1-100)",
        },
    )

    server.register_tool(
        name="investigate_repository",
        func=_investigate_repository,
        description="Gathers comprehensive repository telemetry (issues, PRs, commits, CI) into evidence.",
        parameters={
            "owner": "str (optional): repository owner or organization",
            "repo": "str (required): repository name or 'owner/repo'",
        },
    )

    server.register_tool(
        name="get_project_status",
        func=_get_project_status,
        description="Determines project health status (healthy, warning, blocked, unknown) based on actual evidence.",
        parameters={
            "owner": "str (optional): repository owner or organization",
            "repo": "str (required): repository name or 'owner/repo'",
        },
    )

    server.register_tool(
        name="get_blocker_diagnosis",
        func=_get_blocker_diagnosis,
        description="Diagnoses repository blockers using the Evidence Engine with confidence scoring.",
        parameters={
            "owner": "str (optional): repository owner or organization",
            "repo": "str (required): repository name or 'owner/repo'",
        },
    )

    server.register_tool(
        name="get_recovery_plan",
        func=_get_recovery_plan,
        description="Generates an evidence-grounded, read-only recovery recommendation plan.",
        parameters={
            "owner": "str (optional): repository owner or organization",
            "repo": "str (required): repository name or 'owner/repo'",
        },
    )

    return server
