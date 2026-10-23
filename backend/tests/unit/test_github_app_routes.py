"""Unit tests for GitHub App install and setup callback routes.

Verifies:
1. GET /api/v1/github/install redirect and URL format
2. GET /api/v1/github/setup with valid installation_id
3. GET /api/v1/github/setup with missing installation_id (400)
4. GET /api/v1/github/setup with invalid non-numeric installation_id (400)
5. GET /api/v1/github/setup with HTML accept header (meta-refresh bridge)
6. GET /api/v1/github/status public status reporting without secrets
"""

from unittest.mock import patch

import httpx
import pytest

from app.github.app_auth import github_app_auth
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_github_install_redirect():
    """Verify GET /api/v1/github/install redirects to official GitHub App installation page."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Standard browser redirect
        response = await client.get("/api/v1/github/install", follow_redirects=False)
        assert response.status_code == 302
        location = response.headers["location"]
        assert "https://github.com/apps/" in location
        assert "installations/new" in location

        # 2. JSON format request
        json_resp = await client.get("/api/v1/github/install?format=json")
        assert json_resp.status_code == 200
        data = json_resp.json()
        assert "install_url" in data
        assert "https://github.com/apps/" in data["install_url"]


@pytest.mark.anyio
async def test_github_setup_valid_installation_id():
    """Verify GET /api/v1/github/setup accepts valid installation_id and registers connection safely."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Mock is_configured and get_installation_details to ensure test runs hermetically on CI runners
        with (
            patch.object(type(github_app_auth), "is_configured", property(lambda self: True)),
            patch.object(
                github_app_auth,
                "get_installation_details",
                return_value={"id": 174573260, "account": {"login": "Divakarkr-05", "type": "User"}},
            ),
        ):
            response = await client.get(
                "/api/v1/github/setup?installation_id=174573260&setup_action=install",
                headers={"Accept": "application/json"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["installation_id"] == 174573260
            assert data["setup_action"] == "install"
            assert data["account_login"] == "Divakarkr-05"
            assert "token" not in data
            assert "private_key" not in data
            assert github_app_auth.default_installation_id == 174573260


@pytest.mark.anyio
async def test_github_setup_missing_installation_id():
    """Verify GET /api/v1/github/setup returns 400 when installation_id is missing."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/github/setup", headers={"Accept": "application/json"})
        assert response.status_code == 400
        assert "installation_id" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_github_setup_invalid_installation_id():
    """Verify GET /api/v1/github/setup returns 400 when installation_id is non-numeric or invalid."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Non-numeric string
        resp1 = await client.get(
            "/api/v1/github/setup?installation_id=invalid_abc",
            headers={"Accept": "application/json"},
        )
        assert resp1.status_code == 400
        assert "positive integer" in resp1.json()["detail"]

        # Negative number
        resp2 = await client.get(
            "/api/v1/github/setup?installation_id=-100",
            headers={"Accept": "application/json"},
        )
        assert resp2.status_code == 400


@pytest.mark.anyio
async def test_github_setup_browser_html_response():
    """Verify GET /api/v1/github/setup returns HTML confirmation with redirect to frontend."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        with (
            patch.object(type(github_app_auth), "is_configured", property(lambda self: True)),
            patch.object(
                github_app_auth,
                "get_installation_details",
                return_value={"id": 174573260, "account": {"login": "Divakarkr-05", "type": "User"}},
            ),
        ):
            response = await client.get(
                "/api/v1/github/setup?installation_id=174573260&setup_action=install",
                headers={"Accept": "text/html,application/xhtml+xml"},
            )
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            body = response.text
            assert "GitHub connected successfully" in body
            assert "174573260" in body
            assert "/project?github=connected" in body


@pytest.mark.anyio
async def test_github_status_endpoint():
    """Verify GET /api/v1/github/status exposes connection status safely without leaking secrets."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/github/status")
        assert response.status_code == 200
        data = response.json()
        assert "app_configured" in data
        assert "active_installations" in data
        assert "private_key" not in data
        assert "client_secret" not in data
        assert "token" not in data


@pytest.mark.anyio
async def test_github_setup_when_not_configured():
    """Verify setup succeeds safely even in environments without App private key configured (e.g. CI)."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        with patch.object(type(github_app_auth), "is_configured", property(lambda self: False)):
            response = await client.get(
                "/api/v1/github/setup?installation_id=174573260&setup_action=install",
                headers={"Accept": "application/json"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["installation_id"] == 174573260
            assert data["account_login"] is None
            assert github_app_auth.default_installation_id == 174573260
