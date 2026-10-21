"""Evidence strength and impact scoring."""

from datetime import datetime, timezone

from app.evidence.schemas import Evidence, EvidenceScore


class EvidenceScorer:
    """Calculate the strength of individual evidence items."""

    def score(self, evidence: Evidence) -> EvidenceScore:
        relevance = self._relevance(evidence)
        reliability = self._reliability(evidence)
        recency = self._recency(evidence)

        overall = (
            relevance * 0.40
            + reliability * 0.40
            + recency * 0.20
        )

        return EvidenceScore(
            evidence_id=evidence.id,
            relevance=round(relevance, 3),
            reliability=round(reliability, 3),
            recency=round(recency, 3),
            overall_score=round(overall, 3),
        )

    @staticmethod
    def _relevance(evidence: Evidence) -> float:
        """Estimate how directly the evidence relates to a blocker."""

        if evidence.type.value in {"ci_run", "log", "pull_request"}:
            return 0.90

        if evidence.type.value in {"issue", "commit", "code"}:
            return 0.75

        return 0.50

    @staticmethod
    def _reliability(evidence: Evidence) -> float:
        """Estimate reliability based on the source."""

        if evidence.source_url:
            return 0.95

        if evidence.source_ref:
            return 0.90

        return 0.70

    @staticmethod
    def _recency(evidence: Evidence) -> float:
        """Give newer evidence a higher score."""

        if evidence.timestamp is None:
            return 0.50

        timestamp = evidence.timestamp

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        age_days = (
            datetime.now(timezone.utc) - timestamp
        ).total_seconds() / 86400

        if age_days <= 1:
            return 1.0

        if age_days <= 7:
            return 0.9

        if age_days <= 30:
            return 0.75

        if age_days <= 90:
            return 0.60

        return 0.40# Severity & impact scoring algorithms
