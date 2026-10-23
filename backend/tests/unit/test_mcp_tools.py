"""Unit tests for Model Context Protocol (MCP) tools and server.

Verifies tool registration, input validation, execution with mocked GitHub responses,
and error handling across list_issues, get_pull_request, read_ci_status, and search_code.
"""

from typing import Any, Dict
import httpx
import pytest

from app.core.exceptions import (
    AuthenticationError,
    MCPToolExecutionError,
    ResourceNotFoundError,
    ValidationError,
)
from app.github.client import GitHubClient
from app.mcp import (
    MCPServer,
    create_mcp_server,
    get_pull_request,
    list_issues,
    read_ci_status,
    search_code,
)


@pytest.fixture
def anyio_backend():
    """Restrain anyio tests to the asyncio runner."""
    return "asyncio"


# --- Server Registration Tests ---

def test_mcp_server_registration_and_discovery():
    """Verify default server registers all 4 read-only tools and exposes metadata."""
    server = create_mcp_server()
    tools = server.list_tools()

    tool_names = [t["name"] for t in tools]
    assert "list_issues" in tool_names
    assert "get_pull_request" in tool_names
    assert "read_ci_status" in tool_names
    assert "search_code" in tool_names
    assert "investigate_repository" in tool_names
    assert "get_project_status" in tool_names
    assert "get_blocker_diagnosis" in tool_names
    assert "get_recovery_plan" in tool_names
    assert len(tool_names) == 8


@pytest.mark.anyio
async def test_mcp_server_unregistered_tool():
    """Verify executing an unregistered tool raises MCPToolExecutionError."""
    server = MCPServer()
    with pytest.raises(MCPToolExecutionError) as exc_info:
        await server.execute_tool("nonexistent_tool", foo="bar")
    assert "is not registered" in str(exc_info.value)


# --- list_issues Tool Tests ---

@pytest.mark.anyio
async def test_list_issues_tool_valid():
    """Verify list_issues tool fetches and formats issues with PRs filtered out."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/octocat/Hello-World/issues"
        assert request.url.params["state"] == "open"
        return httpx.Response(
            200,
            json=[
                {"id": 1, "number": 10, "title": "Memory leak", "user": {"login": "dev1"}},
                {"id": 2, "number": 11, "title": "Fix PR", "pull_request": {"url": "..."}},
            ],
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="test-token", client=mock_http)
        results = await list_issues("octocat/Hello-World", state="open", client=client)

        assert len(results) == 1
        assert results[0]["number"] == 10
        assert results[0]["title"] == "Memory leak"
        assert results[0]["author"] == "dev1"
        assert results[0]["repository"] == "octocat/Hello-World"


@pytest.mark.anyio
async def test_list_issues_tool_validation():
    """Verify input validation for repository format, state, and limit."""
    # Invalid repo
    with pytest.raises(ValidationError):
        await list_issues("invalid_repo_name")

    # Invalid state
    with pytest.raises(ValidationError):
        await list_issues("octocat/Hello-World", state="invalid_state")

    # Invalid limit
    with pytest.raises(ValidationError):
        await list_issues("octocat/Hello-World", limit=-5)


# --- get_pull_request Tool Tests ---

@pytest.mark.anyio
async def test_get_pull_request_tool_valid():
    """Verify get_pull_request tool retrieves PR metadata and details."""
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/octocat/Hello-World/pulls/42":
            return httpx.Response(
                200,
                json={
                    "id": 420,
                    "number": 42,
                    "title": "Upgrade dependencies",
                    "state": "open",
                    "head": {"ref": "deps-upgrade", "sha": "abcdef123"},
                    "base": {"ref": "main"},
                    "mergeable": True,
                    "mergeable_state": "clean",
                    "user": {"login": "bot"},
                },
            )
        elif path == "/repos/octocat/Hello-World/pulls/42/files":
            return httpx.Response(200, json=[{"filename": "requirements.txt", "status": "modified"}])
        elif path == "/repos/octocat/Hello-World/pulls/42/reviews":
            return httpx.Response(200, json=[{"user": {"login": "lead"}, "state": "APPROVED"}])
        elif "check-runs" in path or "status" in path:
            return httpx.Response(200, json={"check_runs": [], "total_count": 0, "state": "success"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="test-token", client=mock_http)
        pr = await get_pull_request("octocat/Hello-World", pr_number=42, client=client)

        assert pr["number"] == 42
        assert pr["title"] == "Upgrade dependencies"
        assert pr["head_ref"] == "deps-upgrade"
        assert pr["mergeable"] is True
        assert len(pr["files"]) == 1
        assert pr["review"]["approved"] is True


@pytest.mark.anyio
async def test_get_pull_request_tool_validation_and_404():
    """Verify validation on PR number and 404 handling."""
    with pytest.raises(ValidationError):
        await get_pull_request("octocat/Hello-World", pr_number=0)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="test-token", client=mock_http)
        with pytest.raises(ResourceNotFoundError):
            await get_pull_request("octocat/Hello-World", pr_number=999, client=client)


# --- read_ci_status Tool Tests ---

@pytest.mark.anyio
async def test_read_ci_status_tool_valid():
    """Verify read_ci_status returns structured CI summary and detects blockers."""
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/repos/octocat/Hello-World/actions/runs":
            return httpx.Response(
                200,
                json={
                    "total_count": 1,
                    "workflow_runs": [
                        {
                            "id": 888,
                            "name": "CI",
                            "status": "completed",
                            "conclusion": "failure",
                            "html_url": "https://github.com/octocat/Hello-World/actions/runs/888",
                        }
                    ],
                },
            )
        elif path == "/repos/octocat/Hello-World/actions/runs/888/jobs":
            return httpx.Response(
                200,
                json={
                    "jobs": [
                        {
                            "id": 1,
                            "name": "test",
                            "conclusion": "failure",
                            "steps": [{"name": "pytest", "conclusion": "failure"}],
                        }
                    ]
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="test-token", client=mock_http)
        ci = await read_ci_status("octocat/Hello-World", branch="main", client=client)

        assert ci["repository"] == "octocat/Hello-World"
        assert ci["run_id"] == 888
        assert ci["has_blockers"] is True
        assert ci["total_failed_jobs"] == 1
        assert ci["failed_jobs"][0]["failed_steps"][0]["name"] == "pytest"


# --- search_code Tool Tests ---

@pytest.mark.anyio
async def test_search_code_tool_valid_and_validation():
    """Verify search_code input validation and search snippet return."""
    with pytest.raises(ValidationError):
        await search_code("octocat/Hello-World", query="   ")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search/code"
        assert "repo:octocat/Hello-World" in request.url.params["q"]
        return httpx.Response(
            200,
            json={
                "total_count": 1,
                "incomplete_results": False,
                "items": [
                    {
                        "name": "server.py",
                        "path": "backend/app/mcp/server.py",
                        "sha": "12345",
                        "html_url": "https://github.com/octocat/Hello-World/blob/main/server.py",
                        "repository": {"full_name": "octocat/Hello-World"},
                        "text_matches": [
                            {"fragment": "class MCPServer:\n    pass"}
                        ],
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="test-token", client=mock_http)
        matches = await search_code("octocat/Hello-World", query="MCPServer", client=client)

        assert len(matches) == 1
        assert matches[0]["name"] == "server.py"
        assert "class MCPServer:" in matches[0]["snippets"][0]


# --- Server Invocation Tests ---

@pytest.mark.anyio
async def test_server_invoke_tool_execution():
    """Verify executing registered tools via MCPServer.execute_tool and invoke_tool."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": 1, "number": 5, "title": "Test Issue"}])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="test-token", client=mock_http)
        server = create_mcp_server(client=client)

        # Using execute_tool
        result = await server.execute_tool("list_issues", repo="octocat/Hello-World")
        assert len(result) == 1
        assert result[0]["number"] == 5

        # Using invoke_tool with argument dictionary (Alexa/Agent interface)
        result_invoked = await server.invoke_tool("list_issues", {"repo": "https://github.com/octocat/Hello-World"})
        assert len(result_invoked) == 1
        assert result_invoked[0]["number"] == 5
