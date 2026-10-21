"""Application exception definitions and formatting.

Owned by Member 01 (Cloud, Security & DevOps).
Provides clean, structured, and leak-free exception handling.
"""

from typing import Any, Dict, Optional


class GitlexaException(Exception):
    """Base exception class for all Gitlexa application errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred in Gitlexa.",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Converts exception to safe client-facing dictionary."""
        payload: Dict[str, Any] = {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class ConfigurationError(GitlexaException):
    """Raised when required configurations or environment parameters are missing or invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=500, details=details)


class SecurityError(GitlexaException):
    """Base exception for security and authentication violations."""

    def __init__(self, message: str = "Access denied.", status_code: int = 403, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status_code, details=details)


class AuthenticationError(SecurityError):
    """Raised when authentication credentials are invalid or missing."""

    def __init__(self, message: str = "Authentication required.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=401, details=details)


class AuthorizationError(SecurityError):
    """Raised when an authenticated client lacks permission for an operation."""

    def __init__(self, message: str = "Insufficient permissions.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=403, details=details)


class ResourceNotFoundError(GitlexaException):
    """Raised when a requested resource (project, analysis, issue) does not exist."""

    def __init__(self, resource_name: str, identifier: str):
        message = f"{resource_name} with identifier '{identifier}' was not found."
        super().__init__(message=message, status_code=404, details={"resource": resource_name, "id": identifier})


class ValidationError(GitlexaException):
    """Raised when data fails validation constraints."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=422, details=details)


class RateLimitExceededError(GitlexaException):
    """Raised when rate limits are exceeded."""

    def __init__(self, service: str, retry_after_seconds: Optional[int] = None):
        message = f"Rate limit exceeded for service: {service}."
        details: Dict[str, Any] = {"service": service}
        if retry_after_seconds:
            details["retry_after"] = retry_after_seconds
        super().__init__(message=message, status_code=429, details=details)


class ExternalServiceError(GitlexaException):
    """Base exception for external downstream service errors."""

    def __init__(self, service_name: str, message: str, status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        full_message = f"External service '{service_name}' error: {message}"
        super().__init__(message=full_message, status_code=status_code, details=details)


class GitHubIntegrationError(ExternalServiceError):
    """Raised when GitHub API operations fail."""

    def __init__(self, message: str, status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        super().__init__(service_name="GitHub", message=message, status_code=status_code, details=details)


class BedrockServiceError(ExternalServiceError):
    """Raised when AWS Bedrock model invocation fails."""

    def __init__(self, message: str, status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        super().__init__(service_name="Amazon Bedrock", message=message, status_code=status_code, details=details)


class MCPToolExecutionError(ExternalServiceError):
    """Raised when an MCP tool fails during execution."""

    def __init__(self, tool_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        payload = {"tool_name": tool_name}
        if details:
            payload.update(details)
        super().__init__(service_name=f"MCP Tool: {tool_name}", message=message, status_code=502, details=payload)


class EvidenceError(GitlexaException):
    """Raised when evidence collection, correlation, or scoring encounters an error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=500, details=details)
