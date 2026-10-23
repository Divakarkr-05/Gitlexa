"""Core asynchronous GitHub REST API client for Gitlexa.

Owned by Member 03 (GitHub Integration & Repository Intelligence).
Provides authentication, robust HTTP transport, ETag-based conditional caching,
rate limit inspection, pagination, and unified error mapping.
"""

from __future__ import annotations

import re
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    GitHubIntegrationError,
    RateLimitExceededError,
    ResourceNotFoundError,
)
from app.core.logging import logger


@dataclass
class RateLimitInfo:
    """GitHub API rate limit status snapshot."""

    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_at: Optional[int] = None
    used: Optional[int] = None
    resource: Optional[str] = None


@dataclass
class GitHubCacheEntry:
    """In-memory cache entry for conditional ETag requests."""

    etag: str
    data: Any
    headers: Dict[str, str] = field(default_factory=dict)
    cached_at: float = field(default_factory=time.time)


@dataclass
class GitHubResponse:
    """GitHub API response container with metadata."""

    data: Any
    status_code: int
    headers: Dict[str, str]
    etag: Optional[str] = None
    from_cache: bool = False


class GitHubClient:
    """Asynchronous HTTP client for the GitHub REST API."""

    DEFAULT_BASE_URL: str = "https://api.github.com"
    DEFAULT_API_VERSION: str = "2022-11-28"
    DEFAULT_ACCEPT: str = "application/vnd.github+json"
    DEFAULT_USER_AGENT: str = "Gitlexa-Backend"

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        api_version: str = DEFAULT_API_VERSION,
        timeout: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
        installation_id: Optional[int] = None,
    ) -> None:
        """Initialize GitHub client.

        Args:
            token: Optional GitHub personal access token, OAuth token, or installation token.
                   Defaults to settings.get_github_token_value().
            base_url: GitHub API base URL (default https://api.github.com).
            api_version: GitHub REST API version header (default 2022-11-28).
            timeout: Request timeout in seconds.
            client: Optional pre-configured httpx.AsyncClient (e.g. for testing or pooling).
            installation_id: Optional GitHub App installation ID.
        """
        raw_token = token if token is not None else settings.get_github_token_value()
        self.token: Optional[str] = raw_token if raw_token else None
        self.installation_id: Optional[int] = installation_id or settings.GITHUB_INSTALLATION_ID
        self.base_url: str = base_url.rstrip("/")
        self.api_version: str = api_version
        self.timeout: float = timeout

        self._custom_client: bool = client is not None
        self._client: Optional[httpx.AsyncClient] = client
        self._etag_cache: Dict[str, GitHubCacheEntry] = {}
        self.rate_limit_info: RateLimitInfo = RateLimitInfo()

    async def get_token(self) -> Optional[str]:
        """Resolve current active bearer token, fetching or refreshing App installation token if needed."""
        if self.token:
            return self.token

        from app.github.app_auth import github_app_auth
        if github_app_auth.is_configured:
            try:
                inst_id = self.installation_id or github_app_auth.default_installation_id
                if inst_id:
                    return await github_app_auth.get_installation_token(installation_id=inst_id)
            except Exception as exc:
                logger.debug("Could not resolve GitHub App installation token: %s", exc)

        return settings.get_github_token_value()

    @classmethod
    async def for_installation(cls, installation_id: int) -> "GitHubClient":
        """Factory to create a GitHubClient authenticated for a specific installation."""
        from app.github.app_auth import github_app_auth
        token = await github_app_auth.get_installation_token(installation_id=installation_id)
        return cls(token=token, installation_id=installation_id)

    def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure an active httpx.AsyncClient is available."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
            self._custom_client = False
        return self._client

    async def __aenter__(self) -> "GitHubClient":
        """Async context manager entry."""
        self._ensure_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit with resource cleanup."""
        await self.close()

    async def close(self) -> None:
        """Close HTTP client session if owned by this instance."""
        if self._client is not None and not self._client.is_closed and not self._custom_client:
            await self._client.aclose()

    def clear_cache(self) -> None:
        """Clear all in-memory ETag conditional cache entries."""
        self._etag_cache.clear()

    def _build_headers(
        self,
        custom_headers: Optional[Dict[str, str]] = None,
        token: Optional[str] = None,
    ) -> Dict[str, str]:
        """Construct standard GitHub REST API headers."""
        headers: Dict[str, str] = {
            "Accept": self.DEFAULT_ACCEPT,
            "X-GitHub-Api-Version": self.api_version,
            "User-Agent": self.DEFAULT_USER_AGENT,
        }
        auth_token = token or self.token
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        if custom_headers:
            headers.update(custom_headers)
        return headers

    def _resolve_url(self, endpoint: str) -> str:
        """Resolve full URL from relative path or absolute link."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        clean_endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{clean_endpoint}"

    def _build_cache_key(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate deterministic cache key for conditional caching."""
        if not params:
            return url
        filtered_params = sorted((k, str(v)) for k, v in params.items() if v is not None)
        query = urllib.parse.urlencode(filtered_params)
        return f"{url}?{query}" if query else url

    def _update_rate_limit(self, headers: httpx.Headers) -> None:
        """Parse rate limit headers and update status."""
        limit = headers.get("x-ratelimit-limit")
        remaining = headers.get("x-ratelimit-remaining")
        reset_at = headers.get("x-ratelimit-reset")
        used = headers.get("x-ratelimit-used")
        resource = headers.get("x-ratelimit-resource")

        self.rate_limit_info = RateLimitInfo(
            limit=int(limit) if limit and limit.isdigit() else self.rate_limit_info.limit,
            remaining=int(remaining) if remaining and remaining.isdigit() else self.rate_limit_info.remaining,
            reset_at=int(reset_at) if reset_at and reset_at.isdigit() else self.rate_limit_info.reset_at,
            used=int(used) if used and used.isdigit() else self.rate_limit_info.used,
            resource=resource or self.rate_limit_info.resource,
        )

    def _extract_retry_after(self, response: httpx.Response) -> Optional[int]:
        """Extract retry-after seconds from response headers or reset timestamps."""
        retry_header = response.headers.get("retry-after")
        if retry_header and retry_header.isdigit():
            return int(retry_header)

        reset_header = response.headers.get("x-ratelimit-reset")
        if reset_header and reset_header.isdigit():
            reset_epoch = int(reset_header)
            now_epoch = int(time.time())
            return max(0, reset_epoch - now_epoch)

        return None

    def _extract_error_detail(self, response: httpx.Response) -> Tuple[str, Dict[str, Any]]:
        """Safely parse error response message and details."""
        try:
            body = response.json()
            if isinstance(body, dict):
                msg = body.get("message", response.text or str(response.status_code))
                return str(msg), body
            return response.text or str(response.status_code), {"raw": body}
        except Exception:
            text = response.text or str(response.status_code)
            return text, {"text": text}

    def _handle_error_response(self, response: httpx.Response, endpoint: str) -> None:
        """Map HTTP error status codes to appropriate Gitlexa exceptions."""
        status_code = response.status_code
        error_msg, details = self._extract_error_detail(response)

        # 1. Rate Limit Exceeded (HTTP 429 or HTTP 403 with remaining=0 or rate limit message)
        remaining = response.headers.get("x-ratelimit-remaining")
        is_rate_limited = (
            status_code == 429
            or (status_code == 403 and remaining == "0")
            or (status_code == 403 and "rate limit" in error_msg.lower())
        )
        if is_rate_limited:
            retry_after = self._extract_retry_after(response)
            logger.warning("GitHub rate limit exceeded for %s. Retry after: %s seconds", endpoint, retry_after)
            raise RateLimitExceededError(service="GitHub", retry_after_seconds=retry_after)

        # 2. Authentication Failure (HTTP 401)
        if status_code == 401:
            logger.warning("GitHub authentication failed for %s", endpoint)
            raise AuthenticationError(
                message=f"GitHub authentication failed: {error_msg}",
                details={"status_code": 401, "endpoint": endpoint, "error": error_msg},
            )

        # 3. Resource Not Found (HTTP 404)
        if status_code == 404:
            logger.info("GitHub resource not found: %s", endpoint)
            raise ResourceNotFoundError(resource_name="GitHub Resource", identifier=endpoint)

        # 4. Other 403 Forbidden
        if status_code == 403:
            logger.warning("GitHub permission denied for %s: %s", endpoint, error_msg)
            raise GitHubIntegrationError(
                message=f"GitHub permission denied: {error_msg}",
                status_code=403,
                details={"endpoint": endpoint, **details},
            )

        # 5. Generic 4xx / 5xx HTTP Errors
        logger.error("GitHub API error (%d) for %s: %s", status_code, endpoint, error_msg)
        raise GitHubIntegrationError(
            message=f"GitHub API error ({status_code}): {error_msg}",
            status_code=status_code,
            details={"endpoint": endpoint, **details},
        )

    async def request_raw(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
    ) -> GitHubResponse:
        """Execute HTTP request against GitHub REST API with caching and error handling.

        Args:
            method: HTTP method (GET, POST, PATCH, PUT, DELETE).
            endpoint: Relative path (e.g. '/repos/octocat/hello-world') or absolute URL.
            params: Query parameters.
            json: JSON-serializable request body.
            data: Raw form-encoded data or string.
            headers: Optional custom headers.
            use_cache: Whether to use ETag conditional caching for GET requests.

        Returns:
            GitHubResponse containing parsed data, status code, headers, and metadata.
        """
        client = self._ensure_client()
        url = self._resolve_url(endpoint)
        active_token = await self.get_token()
        request_headers = self._build_headers(headers, token=active_token)
        cache_key = self._build_cache_key(url, params)

        is_get = method.upper() == "GET"
        if is_get and use_cache and cache_key in self._etag_cache:
            cached_entry = self._etag_cache[cache_key]
            request_headers["If-None-Match"] = cached_entry.etag

        logger.debug("GitHub API request: %s %s (params=%s)", method.upper(), url, params)

        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json,
                data=data,
                headers=request_headers,
            )
        except httpx.TimeoutException as exc:
            logger.error("GitHub request timed out for %s: %s", url, str(exc))
            raise GitHubIntegrationError(
                message=f"GitHub request timed out: {exc}",
                status_code=504,
                details={"endpoint": endpoint, "error_type": "timeout"},
            ) from exc
        except httpx.RequestError as exc:
            logger.error("GitHub network request error for %s: %s", url, str(exc))
            raise GitHubIntegrationError(
                message=f"GitHub network communication error: {exc}",
                status_code=502,
                details={"endpoint": endpoint, "error_type": type(exc).__name__},
            ) from exc

        # Update rate limits
        self._update_rate_limit(response.headers)
        logger.debug("GitHub API response: %s %s -> %d", method.upper(), url, response.status_code)

        # Handle 304 Not Modified
        if response.status_code == 304:
            if is_get and cache_key in self._etag_cache:
                logger.debug("GitHub cache hit (304 Not Modified) for %s", url)
                cached = self._etag_cache[cache_key]
                return GitHubResponse(
                    data=cached.data,
                    status_code=304,
                    headers=dict(response.headers),
                    etag=cached.etag,
                    from_cache=True,
                )
            return GitHubResponse(
                data=None,
                status_code=304,
                headers=dict(response.headers),
                etag=response.headers.get("ETag"),
                from_cache=False,
            )

        # Handle errors (HTTP >= 400)
        if response.status_code >= 400:
            self._handle_error_response(response, endpoint)

        # Parse success data
        if response.status_code == 204 or not response.content:
            parsed_data = None
        else:
            try:
                parsed_data = response.json()
            except Exception:
                parsed_data = response.text

        etag = response.headers.get("ETag")
        # Save to ETag cache if successful GET response with ETag
        if is_get and use_cache and etag and response.status_code == 200:
            self._etag_cache[cache_key] = GitHubCacheEntry(
                etag=etag,
                data=parsed_data,
                headers=dict(response.headers),
            )

        return GitHubResponse(
            data=parsed_data,
            status_code=response.status_code,
            headers=dict(response.headers),
            etag=etag,
            from_cache=False,
        )

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
    ) -> Any:
        """Execute request and return parsed response data directly."""
        resp = await self.request_raw(
            method=method,
            endpoint=endpoint,
            params=params,
            json=json,
            data=data,
            headers=headers,
            use_cache=use_cache,
        )
        return resp.data

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
    ) -> Any:
        """Execute asynchronous GET request."""
        return await self.request("GET", endpoint, params=params, headers=headers, use_cache=use_cache)

    async def post(
        self,
        endpoint: str,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute asynchronous POST request."""
        return await self.request("POST", endpoint, params=params, json=json, headers=headers, use_cache=False)

    async def patch(
        self,
        endpoint: str,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute asynchronous PATCH request."""
        return await self.request("PATCH", endpoint, params=params, json=json, headers=headers, use_cache=False)

    async def put(
        self,
        endpoint: str,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute asynchronous PUT request."""
        return await self.request("PUT", endpoint, params=params, json=json, headers=headers, use_cache=False)

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute asynchronous DELETE request."""
        return await self.request("DELETE", endpoint, params=params, headers=headers, use_cache=False)

    @staticmethod
    def parse_link_header(link_header: Optional[str]) -> Dict[str, str]:
        """Parse RFC 5988 Link header into relation -> URL dictionary."""
        links: Dict[str, str] = {}
        if not link_header:
            return links

        for part in link_header.split(","):
            match = re.match(r'<([^>]+)>;\s*rel="([^"]+)"', part.strip())
            if match:
                url, rel = match.groups()
                links[rel] = url
        return links

    async def paginate_pages(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_pages: Optional[int] = None,
        per_page: int = 30,
        use_cache: bool = True,
    ) -> AsyncIterator[List[Any]]:
        """Asynchronously yield each page of list results as a list."""
        page_params = dict(params or {})
        if "per_page" not in page_params:
            page_params["per_page"] = per_page

        current_url: Optional[str] = endpoint
        current_params: Optional[Dict[str, Any]] = page_params
        pages_yielded = 0

        while current_url and (max_pages is None or pages_yielded < max_pages):
            resp = await self.request_raw(
                method="GET",
                endpoint=current_url,
                params=current_params,
                headers=headers,
                use_cache=use_cache,
            )

            data = resp.data
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
                items = data["items"]
            else:
                items = [data] if data is not None else []

            yield items
            pages_yielded += 1

            link_header = resp.headers.get("Link") or resp.headers.get("link")
            links = self.parse_link_header(link_header)

            if "next" in links:
                current_url = links["next"]
                current_params = None  # query params are embedded in the next link
            else:
                if (
                    isinstance(data, list)
                    and len(data) == page_params.get("per_page", per_page)
                    and current_params is not None
                ):
                    current_page = current_params.get("page", 1)
                    current_params["page"] = current_page + 1
                else:
                    break

    async def paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_pages: Optional[int] = None,
        per_page: int = 30,
        use_cache: bool = True,
    ) -> AsyncIterator[Any]:
        """Asynchronously yield individual items across all paginated pages."""
        async for page in self.paginate_pages(
            endpoint=endpoint,
            params=params,
            headers=headers,
            max_pages=max_pages,
            per_page=per_page,
            use_cache=use_cache,
        ):
            for item in page:
                yield item

    async def get_all_pages(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_pages: Optional[int] = None,
        per_page: int = 30,
        use_cache: bool = True,
    ) -> List[Any]:
        """Fetch and aggregate all items across paginated pages into a single list."""
        all_items: List[Any] = []
        async for item in self.paginate(
            endpoint=endpoint,
            params=params,
            headers=headers,
            max_pages=max_pages,
            per_page=per_page,
            use_cache=use_cache,
        ):
            all_items.append(item)
        return all_items
