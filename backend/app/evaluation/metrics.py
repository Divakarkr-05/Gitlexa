"""Evaluation metrics for evidence-backed blocker detection."""

from app.evidence.schemas import BlockerDiagnosis, EvidenceBundle


class EvaluationMetrics:
    """Calculate quality metrics for an investigation."""

    @staticmethod
    def evidence_coverage(
        diagnosis: BlockerDiagnosis,
        bundle: EvidenceBundle,
    ) -> float:
        """Measure how much of the collected evidence supports the diagnosis."""

        if not bundle.evidence:
            return 0.0

        referenced_ids = set(diagnosis.evidence_ids)
        available_ids = {item.id for item in bundle.evidence}

        valid_references = referenced_ids & available_ids

        return round(
            len(valid_references) / len(bundle.evidence),
            3,
        )

    @staticmethod
    def evidence_grounding(
        diagnosis: BlockerDiagnosis,
        bundle: EvidenceBundle,
    ) -> float:
        """Measure whether a diagnosis contains valid evidence references."""

        if not diagnosis.evidence_ids:
            return 0.0

        available_ids = {item.id for item in bundle.evidence}

        valid_count = sum(
            1
            for evidence_id in diagnosis.evidence_ids
            if evidence_id in available_ids
        )

        return round(
            valid_count / len(diagnosis.evidence_ids),
            3,
        )

    @staticmethod
    def confidence_consistency(
        diagnosis: BlockerDiagnosis,
    ) -> float:
        """Check whether confidence is within a valid range."""

        if 0.0 <= diagnosis.confidence <= 1.0:
            return round(diagnosis.confidence, 3)

        return 0.0

    @classmethod
    def evaluate(
        cls,
        diagnosis: BlockerDiagnosis,
        bundle: EvidenceBundle,
    ) -> dict[str, float]:
        """Return all evaluation metrics for one diagnosis."""

        return {
            "evidence_coverage": cls.evidence_coverage(
                diagnosis,
                bundle,
            ),
            "evidence_grounding": cls.evidence_grounding(
                diagnosis,
                bundle,
            ),
            "confidence_consistency": cls.confidence_consistency(
                diagnosis,
            ),
        }