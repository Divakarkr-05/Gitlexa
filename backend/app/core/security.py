"""Security and authentication utilities.

Owned by Member 01 (Cloud, Security & DevOps).
Provides minimal, reusable, and timing-attack resistant helpers.
"""

import re
import secrets
from typing import Optional, Union
from pydantic import SecretStr


def safe_compare(val1: Optional[str], val2: Optional[str]) -> bool:
    """Performs constant-time string comparison to prevent timing side-channel attacks."""
    if val1 is None or val2 is None:
        return False
    return secrets.compare_digest(val1, val2)


def mask_secret(secret: Optional[Union[str, SecretStr]], visible_suffix_len: int = 4) -> str:
    """Safely masks a secret string for logging or UI audit summaries."""
    if not secret:
        return "[NOT SET]"

    raw_value = secret.get_secret_value() if isinstance(secret, SecretStr) else secret
    if not raw_value:
        return "[NOT SET]"

    length = len(raw_value)
    if length <= visible_suffix_len:
        return "*" * length

    masked_prefix = "*" * (length - visible_suffix_len)
    suffix = raw_value[-visible_suffix_len:]
    return f"{masked_prefix}{suffix}"


def sanitize_input(text: Optional[str], max_length: int = 1000) -> str:
    """Sanitizes user and header inputs by stripping control characters and trimming length."""
    if not text:
        return ""

    # Remove null bytes and control characters (except newline and tab)
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
    # Strip leading/trailing whitespaces and enforce length bounds
    return cleaned.strip()[:max_length]


def verify_api_key(
    provided_key: Optional[str],
    expected_key: Optional[Union[str, SecretStr]],
) -> bool:
    """Validates an incoming API key against expected credentials in constant time."""
    if not provided_key or not expected_key:
        return False

    expected_val = (
        expected_key.get_secret_value()
        if isinstance(expected_key, SecretStr)
        else expected_key
    )
    return safe_compare(provided_key, expected_val)


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a cryptographically strong random token."""
    return secrets.token_urlsafe(nbytes)
