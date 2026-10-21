"""Unit tests for Member 01 Security Foundation (backend/app/core/)."""

import logging
import unittest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.logging import SensitiveDataRedactingFilter
from app.core.security import (
    safe_compare,
    mask_secret,
    sanitize_input,
    verify_api_key,
    generate_secure_token,
)
from app.core.exceptions import (
    GitlexaException,
    ConfigurationError,
    SecurityError,
    AuthenticationError,
    GitHubIntegrationError,
    MCPToolExecutionError,
)


class TestCoreSecurity(unittest.TestCase):
    """Tests for core security utilities and configuration."""

    def test_settings_secret_masking(self):
        """Verify that SecretStr never prints raw credentials."""
        token = "ghp_123456789012345678901234567890123456"
        cfg = Settings(GITHUB_TOKEN=token)
        # SecretStr repr should not display raw token
        self.assertNotIn(token, repr(cfg.GITHUB_TOKEN))
        self.assertEqual(cfg.get_github_token_value(), token)

    def test_safe_compare(self):
        """Verify constant-time string comparison."""
        self.assertTrue(safe_compare("secret_token_123", "secret_token_123"))
        self.assertFalse(safe_compare("secret_token_123", "wrong_token"))
        self.assertFalse(safe_compare(None, "token"))
        self.assertFalse(safe_compare("token", None))

    def test_mask_secret(self):
        """Verify secret masking for audit and log display."""
        self.assertEqual(mask_secret(None), "[NOT SET]")
        self.assertEqual(mask_secret(""), "[NOT SET]")
        self.assertEqual(mask_secret("1234"), "****")
        self.assertEqual(mask_secret("secret_token_abcd", 4), "*************abcd")
        self.assertEqual(
            mask_secret(SecretStr("my_sensitive_key_9999"), 4),
            "*****************9999",
        )

    def test_sanitize_input(self):
        """Verify control characters and null bytes are stripped."""
        malicious = "Hello\x00World\x08Test\r\nValid"
        cleaned = sanitize_input(malicious)
        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\x08", cleaned)
        self.assertTrue(cleaned.startswith("HelloWorld"))

    def test_verify_api_key(self):
        """Verify API key validation."""
        expected = SecretStr("correct_api_key")
        self.assertTrue(verify_api_key("correct_api_key", expected))
        self.assertFalse(verify_api_key("invalid_key", expected))
        self.assertFalse(verify_api_key(None, expected))
        self.assertFalse(verify_api_key("key", None))

    def test_generate_secure_token(self):
        """Verify random token generation."""
        t1 = generate_secure_token(16)
        t2 = generate_secure_token(16)
        self.assertNotEqual(t1, t2)
        self.assertGreater(len(t1), 10)


class TestLoggingRedaction(unittest.TestCase):
    """Tests for automatic sensitive data redaction in logging."""

    def setUp(self):
        self.filter = SensitiveDataRedactingFilter()

    def test_redacts_github_tokens(self):
        token = "ghp_123456789012345678901234567890123456"
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg=f"Connecting with token: {token}",
            args=None,
            exc_info=None,
        )
        self.filter.filter(record)
        self.assertNotIn(token, record.msg)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", record.msg)

    def test_redacts_bearer_tokens(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Header Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            args=None,
            exc_info=None,
        )
        self.filter.filter(record)
        self.assertNotIn("eyJhbGci", record.msg)
        self.assertIn("[REDACTED_TOKEN]", record.msg)

    def test_redacts_cookies(self):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Request Cookie: session_id=abc123xyz890;",
            args=None,
            exc_info=None,
        )
        self.filter.filter(record)
        self.assertNotIn("session_id=abc123xyz890", record.msg)
        self.assertIn("[REDACTED_COOKIE]", record.msg)


class TestExceptions(unittest.TestCase):
    """Tests for structured exception hierarchy."""

    def test_gitlexa_exception_dict(self):
        exc = GitlexaException("Test error", status_code=500, details={"ctx": "test"})
        d = exc.to_dict()
        self.assertEqual(d["error"], "GitlexaException")
        self.assertEqual(d["message"], "Test error")
        self.assertEqual(d["status_code"], 500)
        self.assertEqual(d["details"], {"ctx": "test"})

    def test_specialized_exceptions(self):
        auth_err = AuthenticationError("Token expired")
        self.assertEqual(auth_err.status_code, 401)
        self.assertIsInstance(auth_err, SecurityError)

        cfg_err = ConfigurationError("Missing VAR")
        self.assertEqual(cfg_err.status_code, 500)

        gh_err = GitHubIntegrationError("Rate limit reached", status_code=502)
        self.assertEqual(gh_err.status_code, 502)

        mcp_err = MCPToolExecutionError("list_issues", "Timeout")
        self.assertEqual(mcp_err.status_code, 502)
        self.assertEqual(mcp_err.details["tool_name"], "list_issues")


if __name__ == "__main__":
    unittest.main()
