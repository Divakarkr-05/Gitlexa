"""GitHub App authentication and installation token management.

Owned by Member 03 (GitHub Integration & Repository Intelligence).
Provides secure server-side JWT generation using GitHub App RSA private keys,
exchange for installation access tokens, in-memory caching with proactive refresh,
and integration with AWS Secrets Manager or secure local references.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional, Tuple

import httpx
import jwt

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ExternalServiceError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.logging import logger
from app.core.security import mask_secret


def normalize_private_key(raw_key: str) -> str:
    """Normalize a private key string from PEM, escaped newlines, or base64 format."""
    clean_key = raw_key.strip()

    # Check if base64 encoded
    if not clean_key.startswith("-----BEGIN") and len(clean_key) > 64:
        try:
            decoded = base64.b64decode(clean_key).decode("utf-8")
            if "-----BEGIN" in decoded:
                clean_key = decoded.strip()
        except Exception:
            pass

    # Replace literal \n sequences if newlines were collapsed into a single line
    if "\\n" in clean_key and "\n" not in clean_key:
        clean_key = clean_key.replace("\\n", "\n")

    return clean_key.strip()


def load_secret_from_aws(secret_id: str, region_name: Optional[str] = None) -> Optional[str]:
    """Retrieve secret string from AWS Secrets Manager if configured."""
    try:
        import boto3  # type: ignore[import-untyped]
        session = boto3.Session(
            aws_access_key_id=settings.get_aws_access_key(),
            aws_secret_access_key=settings.get_aws_secret_key(),
            region_name=region_name or settings.AWS_REGION,
        )
        client = session.client("secretsmanager")
        response = client.get_secret_value(SecretId=secret_id)
        if "SecretString" in response:
            return str(response["SecretString"])
    except Exception as exc:
        logger.warning("Could not retrieve secret '%s' from AWS Secrets Manager: %s", secret_id, exc)
    return None


class GitHubAppAuth:
    """Server-side authentication manager for GitHub App installations."""

    DEFAULT_BASE_URL: str = "https://api.github.com"
    JWT_EXPIRATION_SECONDS: int = 540  # 9 minutes (GitHub allows max 10 minutes)
    CACHE_EXPIRATION_MARGIN_SECONDS: int = 300  # Refresh 5 minutes before expiry

    def __init__(
        self,
        app_id: Optional[str] = None,
        installation_id: Optional[int] = None,
        private_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        secret_ref: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        """Initialize GitHub App authenticator.

        Args:
            app_id: GitHub App ID (e.g. 5445351).
            installation_id: GitHub App installation ID (e.g. 174573260).
            private_key: Raw private key string (PEM format).
            private_key_path: Path to local private key .pem file.
            secret_ref: AWS Secrets Manager ARN or locator for private key.
            base_url: GitHub API base URL.
        """
        self._app_id = app_id
        self._installation_id = installation_id
        self._private_key = private_key
        self._private_key_path = private_key_path
        self._secret_ref = secret_ref
        self.base_url = base_url.rstrip("/")

        # In-memory token cache: {installation_id: {"token": str, "expires_at": float}}
        self._token_cache: Dict[int, Dict[str, Any]] = {}

    @property
    def app_id(self) -> Optional[str]:
        """Resolve App ID from instance or environment settings."""
        return self._app_id or (str(settings.GITHUB_APP_ID) if settings.GITHUB_APP_ID else None)

    @property
    def default_installation_id(self) -> Optional[int]:
        """Resolve default Installation ID from instance or environment settings."""
        if self._installation_id is not None:
            return self._installation_id
        return settings.GITHUB_INSTALLATION_ID

    @default_installation_id.setter
    def default_installation_id(self, value: Optional[int]) -> None:
        """Set or update the active installation ID."""
        self._installation_id = value

    def get_private_key(self) -> Optional[str]:
        """Load and normalize the RSA private key from env, file path, or Secrets Manager."""
        # 1. Instance or settings private key string
        raw_key = self._private_key or settings.get_github_app_private_key_value()
        if raw_key and raw_key.strip():
            return normalize_private_key(raw_key)

        # 2. Local file path
        key_path = self._private_key_path or settings.GITHUB_APP_PRIVATE_KEY_PATH
        if key_path:
            p = Path(key_path)
            if p.is_file():
                try:
                    content = p.read_text(encoding="utf-8")
                    return normalize_private_key(content)
                except Exception as exc:
                    logger.error("Failed to read private key from path '%s': %s", key_path, exc)

        # 3. AWS Secrets Manager secret reference
        secret_locator = self._secret_ref or settings.GITHUB_APP_SECRET_REF
        if secret_locator:
            secret_val = load_secret_from_aws(secret_locator)
            if secret_val:
                return normalize_private_key(secret_val)

        return None

    @property
    def is_configured(self) -> bool:
        """Verify whether minimum App ID and private key are available."""
        return bool(self.app_id and self.get_private_key())

    def create_jwt(self, expiration_seconds: Optional[int] = None) -> str:
        """Generate a RS256-signed JWT for GitHub App authentication.

        Args:
            expiration_seconds: Lifetime of JWT in seconds (max 600s allowed by GitHub).

        Returns:
            RS256 encoded JWT string.

        Raises:
            AuthenticationError: If app ID or private key are missing or invalid.
        """
        app_id_val = self.app_id
        if not app_id_val:
            raise AuthenticationError(
                message="GitHub App ID is not configured.",
                details={"configured": False},
            )

        private_key_pem = self.get_private_key()
        if not private_key_pem:
            raise AuthenticationError(
                message="GitHub App private key could not be loaded from environment, file, or Secrets Manager.",
                details={"app_id": app_id_val},
            )

        now = int(time.time())
        exp_duration = expiration_seconds or self.JWT_EXPIRATION_SECONDS
        payload = {
            "iat": now - 60,  # 60s clock drift buffer
            "exp": now + exp_duration,
            "iss": app_id_val,
        }

        try:
            token = jwt.encode(payload, private_key_pem, algorithm="RS256")
            return str(token)
        except Exception as exc:
            logger.error("Failed to sign GitHub App JWT: %s", exc)
            raise AuthenticationError(
                message="Failed to sign GitHub App JWT with provided private key.",
                details={"error": str(exc)},
            ) from exc

    def invalidate_cached_token(self, installation_id: Optional[int] = None) -> None:
        """Clear cached installation token to force a refresh on next call."""
        target_id = installation_id or self.default_installation_id
        if target_id and target_id in self._token_cache:
            del self._token_cache[target_id]

    async def get_installation_token(
        self,
        installation_id: Optional[int] = None,
        force_refresh: bool = False,
        client: Optional[httpx.AsyncClient] = None,
    ) -> str:
        """Retrieve an installation access token, using cached token if still valid.

        Args:
            installation_id: Target installation ID (defaults to settings.GITHUB_INSTALLATION_ID).
            force_refresh: When True, bypasses cache and requests a new token.
            client: Optional httpx.AsyncClient for request execution.

        Returns:
            GitHub installation access token string.

        Raises:
            ValidationError: If installation ID is missing.
            AuthenticationError: If GitHub rejects JWT or installation credentials.
            ResourceNotFoundError: If installation ID does not exist on GitHub.
        """
        target_id = installation_id or self.default_installation_id
        if not target_id:
            raise ValidationError(
                message="No GitHub App installation ID provided or configured.",
                details={"app_id": self.app_id},
            )

        now = time.time()

        # Check in-memory cache
        if not force_refresh and target_id in self._token_cache:
            cached = self._token_cache[target_id]
            if cached.get("expires_at", 0) - now > self.CACHE_EXPIRATION_MARGIN_SECONDS:
                return str(cached["token"])

        # Generate JWT and request installation access token from GitHub
        jwt_token = self.create_jwt()
        endpoint = f"{self.base_url}/app/installations/{target_id}/access_tokens"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt_token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Gitlexa-Backend",
        }

        if client is not None:
            resp = await client.post(endpoint, headers=headers)
            return self._process_token_response(resp, target_id)
        else:
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                resp = await http_client.post(endpoint, headers=headers)
                return self._process_token_response(resp, target_id)

    def _process_token_response(self, response: httpx.Response, installation_id: int) -> str:
        """Handle GitHub access token response and cache the result safely."""
        if response.status_code == 404:
            raise ResourceNotFoundError(
                resource_name="GitHub App Installation",
                identifier=str(installation_id),
            )
        if response.status_code in (401, 403):
            raise AuthenticationError(
                message=f"GitHub rejected App authentication for installation {installation_id}: {response.text}",
                details={"status_code": response.status_code},
            )
        if response.status_code >= 400:
            raise ExternalServiceError(
                service_name="GitHub",
                message=f"Failed to generate installation access token (status {response.status_code})",
                status_code=502,
                details={"response": response.text},
            )

        data = response.json()
        token = data.get("token")
        if not token:
            raise ExternalServiceError(
                service_name="GitHub",
                message="GitHub returned an empty installation access token.",
                status_code=502,
            )

        # Parse ISO-8601 expiry or fallback to 1 hour
        expires_at_epoch = time.time() + 3600
        raw_expires_at = data.get("expires_at")
        if raw_expires_at:
            try:
                # Handle RFC 3339 / ISO 8601 string
                dt = datetime.fromisoformat(raw_expires_at.replace("Z", "+00:00"))
                expires_at_epoch = dt.timestamp()
            except Exception:
                pass

        self._token_cache[installation_id] = {
            "token": token,
            "expires_at": expires_at_epoch,
            "permissions": data.get("permissions", {}),
            "repository_selection": data.get("repository_selection", "all"),
        }

        logger.info(
            "Successfully acquired GitHub App installation token for installation %d (expires in ~%ds)",
            installation_id,
            int(expires_at_epoch - time.time()),
        )
        return str(token)

    async def get_installation_details(
        self,
        installation_id: Optional[int] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        """Fetch installation metadata using GitHub App JWT authentication."""
        target_id = installation_id or self.default_installation_id
        if not target_id:
            raise ValidationError(message="No GitHub App installation ID provided.")

        jwt_token = self.create_jwt()
        endpoint = f"{self.base_url}/app/installations/{target_id}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt_token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Gitlexa-Backend",
        }

        if client is not None:
            resp = await client.get(endpoint, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                resp = await http_client.get(endpoint, headers=headers)

        if resp.status_code == 404:
            raise ResourceNotFoundError("GitHub App Installation", str(target_id))
        if resp.status_code >= 400:
            raise ExternalServiceError("GitHub", f"Failed to get installation details: {resp.text}", 502)

        data = resp.json()
        return data if isinstance(data, dict) else {}

    def get_public_status(self) -> Dict[str, Any]:
        """Return non-sensitive status summary for health/audit checks."""
        key_configured = bool(self.get_private_key())
        return {
            "app_configured": self.is_configured,
            "app_id": self.app_id,
            "installation_id": self.default_installation_id,
            "private_key_configured": key_configured,
            "has_cached_token": bool(self.default_installation_id and self.default_installation_id in self._token_cache),
        }


# Global singleton instance
github_app_auth: GitHubAppAuth = GitHubAppAuth()
