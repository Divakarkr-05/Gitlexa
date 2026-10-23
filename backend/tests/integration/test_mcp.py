"""Integration tests for the MCP Server subsystem."""

import pytest
from app.mcp import MCPServer, create_mcp_server


def test_mcp_server_initialization_and_tool_registry():
    """Verify MCP server initializes with all Phase 4 read-only tools."""
    server = create_mcp_server()
    assert isinstance(server, MCPServer)

    tools = server.list_tools()
    tool_names = {t["name"] for t in tools}

    expected_tools = {"list_issues", "get_pull_request", "read_ci_status", "search_code"}
    assert expected_tools.issubset(tool_names)
