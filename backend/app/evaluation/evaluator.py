"""End-to-end evaluation of Gitlexa blocker detection."""

from app.evidence.blocker_detection import BlockerDetector
from app.evidence.correlation import EvidenceCorrelator
from app.evidence.schemas import BlockerDiagnosis, EvidenceBundle
from app.evaluation.metrics import EvaluationMetrics


class InvestigationEvaluator:
    """Evaluate whether an investigation produces grounded diagnoses."""

    def __init__(self) -> None:
        self.correlator = EvidenceCorrelator()
        self.detector = BlockerDetector()

    def evaluate(
        self,
        bundle: EvidenceBundle,
    ) -> dict:
        """Run correlation, blocker detection, and evaluation."""

        correlations = self.correlator.correlate(bundle)

        diagnoses = self.detector.detect(
            bundle,
            correlations,
        )

        results = [
            self._evaluate_diagnosis(
                diagnosis,
                bundle,
            )
            for diagnosis in diagnoses
        ]

        passed = bool(results) and all(
            result["grounded"]
            and result["metrics"]["evidence_grounding"] >= 0.90
            and result["confidence"] >= 0.70
            for result in results
        )

        return {
            "repository": bundle.repository,
            "evidence_count": len(bundle.evidence),
            "correlation_count": len(correlations),
            "diagnosis_count": len(diagnoses),
            "passed": passed,
            "results": results,
        }

    @staticmethod
    def _evaluate_diagnosis(
        diagnosis: BlockerDiagnosis,
        bundle: EvidenceBundle,
    ) -> dict:
        """Evaluate one blocker diagnosis."""

        metrics = EvaluationMetrics.evaluate(
            diagnosis,
            bundle,
        )

        return {
            "blocker": diagnosis.blocker,
            "confidence": diagnosis.confidence,
            "evidence_ids": diagnosis.evidence_ids,
            "metrics": metrics,
            "grounded": metrics["evidence_grounding"] == 1.0,
        }
# CI validation
