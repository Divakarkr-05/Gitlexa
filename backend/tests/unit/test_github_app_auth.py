"""Unit tests for GitHub App authentication and installation token management.

Verifies RS256 JWT generation, installation access token exchange, in-memory caching,
error handling, and seamless integration with GitHubClient.
"""

import time
from typing import Any, Dict
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import httpx
import jwt
import pytest

from app.core.exceptions import AuthenticationError, ResourceNotFoundError, ValidationError
from app.github.app_auth import GitHubAppAuth, normalize_private_key
from app.github.client import GitHubClient


@pytest.fixture(scope="module")
def rsa_keypair():
    """Generate an ephemeral RSA key pair for testing RS256 JWTs."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_normalize_private_key_with_escaped_newlines(rsa_keypair):
    """Verify private key with escaped \\n sequences is normalized."""
    private_pem, _ = rsa_keypair
    escaped = private_pem.replace("\n", "\\n")
    normalized = normalize_private_key(escaped)
    assert "-----BEGIN PRIVATE KEY-----" in normalized
    assert "\n" in normalized


def test_github_app_auth_jwt_creation(rsa_keypair):
    """Verify GitHubAppAuth creates valid RS256 JWT with correct claims."""
    private_pem, public_pem = rsa_keypair
    auth = GitHubAppAuth(
        app_id="5445351",
        installation_id=174573260,
        private_key=private_pem,
    )

    assert auth.is_configured is True
    jwt_token = auth.create_jwt()

    # Decode using public key to verify signature and claims
    decoded = jwt.decode(jwt_token, public_pem, algorithms=["RS256"])
    assert decoded["iss"] == "5445351"
    assert decoded["exp"] > int(time.time())
    assert decoded["iat"] <= int(time.time())


def test_github_app_auth_missing_credentials():
    """Verify AuthenticationError is raised if App ID or private key is missing."""
    with patch("app.github.app_auth.settings.GITHUB_APP_PRIVATE_KEY", None), \
         patch("app.github.app_auth.settings.GITHUB_APP_PRIVATE_KEY_PATH", None), \
         patch("app.github.app_auth.settings.GITHUB_APP_SECRET_REF", None):
        auth_no_key = GitHubAppAuth(app_id="5445351", private_key=None)
        with pytest.raises(AuthenticationError):
            auth_no_key.create_jwt()

    with patch("app.github.app_auth.settings.GITHUB_APP_ID", None):
        auth_no_id = GitHubAppAuth(app_id=None, private_key="dummy")
        with pytest.raises(AuthenticationError):
            auth_no_id.create_jwt()


@pytest.mark.anyio
async def test_get_installation_token_exchange(rsa_keypair):
    """Verify exchange of JWT for installation token and proper caching."""
    private_pem, _ = rsa_keypair
    auth = GitHubAppAuth(
        app_id="5445351",
        installation_id=174573260,
        private_key=private_pem,
    )

    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        assert request.url.path == "/app/installations/174573260/access_tokens"
        assert "Bearer " in request.headers["authorization"]
        assert request.headers["x-github-api-version"] == "2022-11-28"
        return httpx.Response(
            201,
            json={
                "token": "ghs_mockInstallationToken12345",
                "expires_at": "2030-01-01T00:00:00Z",
                "permissions": {"issues": "write", "pull_requests": "write"},
                "repository_selection": "selected",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        # First call: makes network request
        token1 = await auth.get_installation_token(client=mock_http)
        assert token1 == "ghs_mockInstallationToken12345"
        assert call_count == 1

        # Second call: uses in-memory cache, no new HTTP request
        token2 = await auth.get_installation_token(client=mock_http)
        assert token2 == "ghs_mockInstallationToken12345"
        assert call_count == 1

        # Force refresh: bypasses cache
        token3 = await auth.get_installation_token(force_refresh=True, client=mock_http)
        assert token3 == "ghs_mockInstallationToken12345"
        assert call_count == 2


@pytest.mark.anyio
async def test_get_installation_token_404(rsa_keypair):
    """Verify ResourceNotFoundError when installation does not exist."""
    private_pem, _ = rsa_keypair
    auth = GitHubAppAuth(
        app_id="5445351",
        installation_id=999999,
        private_key=private_pem,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        with pytest.raises(ResourceNotFoundError):
            await auth.get_installation_token(client=mock_http)


@pytest.mark.anyio
async def test_github_client_uses_installation_token_dynamically(rsa_keypair):
    """Verify GitHubClient automatically resolves installation token when no token is passed."""
    private_pem, _ = rsa_keypair
    test_auth = GitHubAppAuth(
        app_id="5445351",
        installation_id=174573260,
        private_key=private_pem,
    )

    # Pre-cache a token in test_auth
    test_auth._token_cache[174573260] = {
        "token": "ghs_dynamicTestInstallationToken",
        "expires_at": time.time() + 3600,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("authorization") == "Bearer ghs_dynamicTestInstallationToken"
        return httpx.Response(200, json={"id": 1, "name": "Gitlexa"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_http:
        with patch("app.github.app_auth.github_app_auth", test_auth):
            # Create client with no token provided
            client = GitHubClient(token="", client=mock_http, installation_id=174573260)
            data = await client.get("/repos/Divakarkr-05/Gitlexa")
            assert isinstance(data, dict)
            assert data["name"] == "Gitlexa"
