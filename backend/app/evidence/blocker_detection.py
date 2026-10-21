"""Detect likely project blockers from correlated evidence."""

from app.evidence.schemas import (
    BlockerDiagnosis,
    Correlation,
    EvidenceBundle,
)


class BlockerDetector:
    """Convert correlated evidence into an evidence-backed diagnosis."""

    def detect(
        self,
        bundle: EvidenceBundle,
        correlations: list[Correlation],
    ) -> list[BlockerDiagnosis]:
        diagnoses: list[BlockerDiagnosis] = []

        failed_ci = [
            item
            for item in bundle.evidence
            if item.type.value == "ci_run"
            and self._is_failed(item)
        ]

        for ci in failed_ci:
            related_ids = [
                evidence_id
                for correlation in correlations
                if ci.id in correlation.evidence_ids
                for evidence_id in correlation.evidence_ids
                if evidence_id != ci.id
            ]

            diagnoses.append(
                BlockerDiagnosis(
                    blocker="CI pipeline failure",
                    explanation=(
                        f"CI evidence indicates that the pipeline is failing: "
                        f"{ci.title}"
                    ),
                    evidence_ids=[ci.id, *related_ids],
                    correlations=[
                        correlation.id
                        for correlation in correlations
                        if ci.id in correlation.evidence_ids
                    ],
                    confidence=0.90 if related_ids else 0.75,
                    recommended_actions=[
                        "Inspect the failed CI job logs.",
                        "Identify the first failing step.",
                        "Check the commits associated with the failing run.",
                        "Apply and validate the smallest corrective change.",
                        "Re-run CI and verify that the failure is resolved.",
                    ],
                )
            )

        return diagnoses

    @staticmethod
    def _is_failed(evidence) -> bool:
        """Determine whether CI evidence represents a failed run."""

        metadata = evidence.metadata

        status = str(
            metadata.get("status")
            or metadata.get("conclusion")
            or metadata.get("state")
            or ""
        ).lower()

        return status in {
            "failure",
            "failed",
            "failure",
            "cancelled",
            "timed_out",
            "error",
        }# Blocker Detection algorithms
