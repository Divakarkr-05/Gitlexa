"""GitHub API HTTP client and base transport.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Provides authenticated asynchronous HTTP access to the GitHub REST API.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional
import httpx

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ExternalServiceError,
    RateLimitExceededError,
    ResourceNotFoundError,
    ValidationError,
)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_HEADERS: Dict[str, str] = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


class GitHubClient:
    """Asynchronous client for interacting with GitHub REST APIs."""

    def __init__(
        self,
        token: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        base_url: str = GITHUB_API_BASE,
    ) -> None:
        self.token = token if token is not None else settings.get_github_token_value()
        self._client = client
        self.base_url = base_url.rstrip("/")

    def get_headers(self) -> Dict[str, str]:
        headers = dict(GITHUB_API_HEADERS)
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response_status(self, response: httpx.Response) -> None:
        if response.status_code == 401:
            raise AuthenticationError(
                message="GitHub authentication failed. Token is missing or invalid.",
                details={"status_code": 401, "response": response.text},
            )
        if response.status_code == 403:
            if "rate limit" in response.text.lower():
                raise RateLimitExceededError(service="GitHub")
            raise AuthenticationError(
                message="GitHub permission denied or rate limit exceeded.",
                details={"status_code": 403, "response": response.text},
            )
        if response.status_code == 404:
            raise ResourceNotFoundError(
                resource_name="GitHub Resource",
                identifier=str(response.url),
            )
        if response.status_code == 422:
            raise ValidationError(
                message=f"GitHub validation error: {response.text}",
                details={"status_code": 422, "response": response.text},
            )
        if response.status_code >= 400:
            raise ExternalServiceError(
                service_name="GitHub",
                message=f"GitHub API returned error {response.status_code}: {response.text}",
                status_code=502,
                details={"status_code": response.status_code, "response": response.text},
            )

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        url = (
            endpoint
            if endpoint.startswith("http://") or endpoint.startswith("https://")
            else f"{self.base_url}/{endpoint.lstrip('/')}"
        )
        merged_headers = self.get_headers()
        if headers:
            merged_headers.update(headers)

        if self._client is not None:
            resp = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=merged_headers,
            )
            self._handle_response_status(resp)
            return resp
        else:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=merged_headers,
                )
                self._handle_response_status(resp)
                return resp

    async def get(
        self,
        endpoint: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        return await self.request("GET", endpoint, params=params, headers=headers)

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> GitHubClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()
