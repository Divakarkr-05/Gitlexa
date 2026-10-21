"""Safe application logging with automated sensitive data redaction.

Owned by Member 01 (Cloud, Security & DevOps).
Ensures secrets, tokens, authorization headers, and credentials are never logged.
"""

import logging
import re
import sys
from typing import Pattern, List, Tuple


class SensitiveDataRedactingFilter(logging.Filter):
    """Logging filter that scrubs tokens, credentials, and sensitive patterns from log records."""

    PATTERNS: List[Tuple[Pattern, str]] = [
        # GitHub tokens (classic PATs and fine-grained PATs)
        (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "[REDACTED_GITHUB_TOKEN]"),
        (re.compile(r"github_pat_[a-zA-Z0-9_]{82}"), "[REDACTED_GITHUB_PAT]"),
        (re.compile(r"gho_[a-zA-Z0-9]{36}"), "[REDACTED_GITHUB_OAUTH]"),

        # AWS Access Keys
        (re.compile(r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])"), "[REDACTED_AWS_KEY]"),

        # Authorization headers & Bearer tokens
        (
            re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[a-zA-Z0-9_\-\.]{10,}"),
            r"\1[REDACTED_TOKEN]",
        ),
        (
            re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{10,}"),
            r"\1[REDACTED_TOKEN]",
        ),

        # Key-value secret patterns (e.g., api_key=..., secret=..., password=...)
        (
            re.compile(
                r"(?i)(api[_-]?key|secret[_-]?key|password|client[_-]?secret|private[_-]?key)\s*[:=]\s*['\"]?([^'\"\s,]+)"
            ),
            r"\1=[REDACTED]",
        ),

        # Cookies and session headers
        (
            re.compile(r"(?i)(cookie\s*[:=]\s*)[^\r\n;]+"),
            r"\1[REDACTED_COOKIE]",
        ),
    ]

    def _sanitize(self, text: str) -> str:
        for pattern, replacement in self.PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._sanitize(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._sanitize(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._sanitize(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configures application logger with sensitive data filtering."""
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers on reload
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataRedactingFilter())
        root_logger.addHandler(handler)
    else:
        # Attach filter to existing handlers
        for h in root_logger.handlers:
            h.addFilter(SensitiveDataRedactingFilter())

    app_logger = logging.getLogger("gitlexa")
    app_logger.setLevel(numeric_level)
    return app_logger


# Default application logger instance
logger = setup_logging()
