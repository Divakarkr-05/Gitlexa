# Evidence Collector from GitHub & CI
"""Collect and normalize evidence from GitHub and CI sources."""

from typing import Any

from app.evidence.schemas import Evidence, EvidenceBundle, EvidenceType


class EvidenceCollector:
    """Converts raw GitHub/CI observations into normalized evidence."""

    def __init__(self, repository: str) -> None:
        self.repository = repository

    def collect(
        self,
        *,
        issues: list[dict[str, Any]] | None = None,
        pull_requests: list[dict[str, Any]] | None = None,
        ci_runs: list[dict[str, Any]] | None = None,
        commits: list[dict[str, Any]] | None = None,
        code_findings: list[dict[str, Any]] | None = None,
        logs: list[dict[str, Any]] | None = None,
    ) -> EvidenceBundle:
        """Build an evidence bundle from raw source observations."""

        bundle = EvidenceBundle(repository=self.repository)

        self._add_items(bundle, issues or [], EvidenceType.ISSUE)
        self._add_items(bundle, pull_requests or [], EvidenceType.PULL_REQUEST)
        self._add_items(bundle, ci_runs or [], EvidenceType.CI_RUN)
        self._add_items(bundle, commits or [], EvidenceType.COMMIT)
        self._add_items(bundle, code_findings or [], EvidenceType.CODE)
        self._add_items(bundle, logs or [], EvidenceType.LOG)

        return bundle

    def _add_items(
        self,
        bundle: EvidenceBundle,
        items: list[dict[str, Any]],
        evidence_type: EvidenceType,
    ) -> None:
        """Normalize source records into Evidence objects."""

        for index, item in enumerate(items):
            evidence_id = str(
                item.get("id")
                or item.get("number")
                or f"{evidence_type.value}-{index + 1}"
            )

            evidence = Evidence(
                id=evidence_id,
                type=evidence_type,
                title=str(
                    item.get("title")
                    or item.get("name")
                    or item.get("message")
                    or f"{evidence_type.value.title()} evidence"
                ),
                description=str(
                    item.get("description")
                    or item.get("body")
                    or item.get("message")
                    or ""
                ),
                source_url=item.get("html_url") or item.get("url"),
                source_ref=item.get("ref") or item.get("sha"),
                repository=self.repository,
                author=self._extract_author(item),
                timestamp=item.get("timestamp")
                or item.get("created_at")
                or item.get("updated_at"),
                metadata=item,
            )

            bundle.add(evidence)

    @staticmethod
    def _extract_author(item: dict[str, Any]) -> str | None:
        """Extract an author/login from common GitHub response shapes."""

        author = item.get("author")

        if isinstance(author, dict):
            return author.get("login") or author.get("name")

        if isinstance(author, str):
            return author

        user = item.get("user")

        if isinstance(user, dict):
            return user.get("login") or user.get("name")

        return None