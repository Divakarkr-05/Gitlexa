"""Adapter between GitHub data providers and the Evidence Engine."""

from typing import Any

from app.evidence.collector import EvidenceCollector
from app.evidence.schemas import EvidenceBundle


class GitHubEvidenceAdapter:
    """Convert GitHub provider results into normalized evidence."""

    def collect(
        self,
        repository: str,
        *,
        issues: list[dict[str, Any]] | None = None,
        pull_requests: list[dict[str, Any]] | None = None,
        ci_runs: list[dict[str, Any]] | None = None,
        commits: list[dict[str, Any]] | None = None,
        code_findings: list[dict[str, Any]] | None = None,
        logs: list[dict[str, Any]] | None = None,
    ) -> EvidenceBundle:
        collector = EvidenceCollector(repository)

        return collector.collect(
            issues=issues,
            pull_requests=pull_requests,
            ci_runs=ci_runs,
            commits=commits,
            code_findings=code_findings,
            logs=logs,
        )