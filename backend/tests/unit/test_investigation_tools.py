"""Unit tests for Gitlexa MVP investigation tools.

Verifies:
1. Tool registration on MCPServer
2. Input validation (owner and repo formats)
3. Structured output schemas across investigate_repository, get_project_status,
   get_blocker_diagnosis, and get_recovery_plan
4. GitHub failure and empty state handling (no fabricated evidence)
5. Blocker diagnosis with confidence between 0.0 and 1.0
6. Read-only recovery plan generation
"""

import httpx
import pytest

from app.core.exceptions import ValidationError
from app.github.client import GitHubClient
from app.mcp import (
    create_mcp_server,
    get_blocker_diagnosis,
    get_project_status,
    get_recovery_plan,
    investigate_repository,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_investigation_tools_registered_in_mcp():
    """Verify all 4 investigation tools are properly registered with schemas."""
    server = create_mcp_server()
    tools = server.list_tools()
    tool_map = {t["name"]: t for t in tools}

    assert "investigate_repository" in tool_map
    assert "get_project_status" in tool_map
    assert "get_blocker_diagnosis" in tool_map
    assert "get_recovery_plan" in tool_map

    for name in ("investigate_repository", "get_project_status", "get_blocker_diagnosis", "get_recovery_plan"):
        assert "owner" in tool_map[name]["parameters"]
        assert "repo" in tool_map[name]["parameters"]


@pytest.mark.anyio
async def test_input_validation():
    """Verify missing or invalid repository parameters raise ValidationError."""
    with pytest.raises(ValidationError):
        await investigate_repository(owner="", repo="")

    with pytest.raises(ValidationError):
        await get_project_status(owner="", repo="")

    with pytest.raises(ValidationError):
        await get_blocker_diagnosis(owner="", repo="")

    with pytest.raises(ValidationError):
        await get_recovery_plan(owner="", repo="")


@pytest.mark.anyio
async def test_investigate_repository_structured_output():
    """Verify investigate_repository collects and structures actual GitHub telemetry."""
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/issues" in path:
            return httpx.Response(200, json=[{"id": 1, "number": 10, "title": "Database connection pool exhausted"}])
        elif "/pulls" in path:
            return httpx.Response(200, json=[{"id": 2, "number": 20, "title": "Upgrade async client"}])
        elif "/commits" in path:
            return httpx.Response(200, json=[{"sha": "c1a2b3", "commit": {"message": "fix: update db pool config"}}])
        elif "/actions/runs" in path:
            return httpx.Response(200, json={"total_count": 1, "workflow_runs": [{"id": 999, "name": "CI", "status": "completed", "conclusion": "success"}]})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="mock-token", client=mock_http)
        result = await investigate_repository(owner="Divakarkr-05", repo="Gitlexa", client=client)

        assert result["repository"] == "Divakarkr-05/Gitlexa"
        assert len(result["issues"]) == 1
        assert result["issues"][0]["number"] == 10
        assert len(result["pull_requests"]) == 1
        assert len(result["commits"]) == 1
        assert len(result["ci_status"]) == 1
        assert result["evidence_count"] >= 3


@pytest.mark.anyio
async def test_no_fabricated_evidence_on_empty_repo():
    """Verify empty GitHub response returns empty evidence without fabricating data."""
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/actions/runs" in path:
            return httpx.Response(200, json={"total_count": 0, "workflow_runs": []})
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="mock-token", client=mock_http)
        result = await investigate_repository(owner="Divakarkr-05", repo="Gitlexa", client=client)

        assert result["issues"] == []
        assert result["pull_requests"] == []
        assert result["commits"] == []
        assert result["ci_status"] == []
        assert result["evidence_count"] == 0

        # Diagnosis on empty repo
        diagnosis = await get_blocker_diagnosis(owner="Divakarkr-05", repo="Gitlexa", client=client)
        assert diagnosis["blocked"] is False
        assert diagnosis["confidence"] == 0.0
        assert diagnosis["evidence"] == []


@pytest.mark.anyio
async def test_blocker_diagnosis_and_recovery_plan_when_ci_fails():
    """Verify complete chain: failed CI produces blocker diagnosis and read-only recovery plan."""
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/actions/runs" in path:
            return httpx.Response(
                200,
                json={
                    "total_count": 1,
                    "workflow_runs": [
                        {
                            "id": 501,
                            "name": "Backend Quality & Tests",
                            "status": "completed",
                            "conclusion": "failure",
                            "html_url": "https://github.com/Divakarkr-05/Gitlexa/actions/runs/501",
                        }
                    ],
                },
            )
        elif "/issues" in path or "/pulls" in path:
            return httpx.Response(200, json=[])
        elif "/commits" in path:
            return httpx.Response(200, json=[{"sha": "abcdef123", "commit": {"message": "refactor mcp tools"}}])
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="mock-token", client=mock_http)

        # 1. Project Status -> blocked
        status = await get_project_status(owner="Divakarkr-05", repo="Gitlexa", client=client)
        assert status["status"] == "blocked"
        assert "fail" in status["reason"].lower() or "block" in status["reason"].lower()
        assert len(status["evidence"]) >= 1

        # 2. Blocker Diagnosis -> blocked with confidence
        diagnosis = await get_blocker_diagnosis(owner="Divakarkr-05", repo="Gitlexa", client=client)
        assert diagnosis["blocked"] is True
        assert "CI pipeline failure" in diagnosis["blocker"]
        assert 0.0 <= diagnosis["confidence"] <= 1.0
        assert len(diagnosis["evidence"]) >= 1

        # 3. Recovery Plan -> read-only steps
        plan = await get_recovery_plan(owner="Divakarkr-05", repo="Gitlexa", client=client)
        assert "steps" in plan
        assert len(plan["steps"]) >= 3
        # Ensure all steps are read-only suggestions
        for step in plan["steps"]:
            assert "step" in step
            assert "action" in step
            assert "reason" in step
            assert "evidence" in step
            # Confirm no destructive actions are being executed
            assert "push" not in step["action"].lower() or "validated" in step["action"].lower()


@pytest.mark.anyio
async def test_recovery_plan_when_healthy():
    """Verify recovery plan indicates clean health when no blockers exist."""
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/actions/runs" in path:
            return httpx.Response(
                200,
                json={
                    "total_count": 1,
                    "workflow_runs": [
                        {
                            "id": 100,
                            "name": "CI",
                            "status": "completed",
                            "conclusion": "success",
                        }
                    ],
                },
            )
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        client = GitHubClient(token="mock-token", client=mock_http)

        status = await get_project_status(owner="Divakarkr-05", repo="Gitlexa", client=client)
        assert status["status"] == "healthy"

        diagnosis = await get_blocker_diagnosis(owner="Divakarkr-05", repo="Gitlexa", client=client)
        assert diagnosis["blocked"] is False

        plan = await get_recovery_plan(owner="Divakarkr-05", repo="Gitlexa", client=client)
        assert len(plan["steps"]) == 1
        assert "clean" in plan["steps"][0]["evidence"].lower() or "healthy" in plan["steps"][0]["reason"].lower()
