"""Format evidence and blocker diagnoses for API, UI, and voice output."""

from app.evidence.schemas import BlockerDiagnosis, EvidenceBundle


class EvidenceFormatter:
    """Create consistent human-readable representations."""

    def format_ui(
        self,
        bundle: EvidenceBundle,
        diagnoses: list[BlockerDiagnosis],
    ) -> dict:
        """Format evidence for the web UI."""

        return {
            "repository": bundle.repository,
            "evidence_count": len(bundle.evidence),
            "evidence": [
                {
                    "id": item.id,
                    "type": item.type.value,
                    "title": item.title,
                    "description": item.description,
                    "source_url": item.source_url,
                    "score": round(
                        (
                            item.relevance_score
                            + item.reliability_score
                        )
                        / 2,
                        3,
                    ),
                }
                for item in bundle.evidence
            ],
            "diagnoses": [
                {
                    "blocker": diagnosis.blocker,
                    "explanation": diagnosis.explanation,
                    "confidence": diagnosis.confidence,
                    "evidence_ids": diagnosis.evidence_ids,
                    "recommended_actions": diagnosis.recommended_actions,
                }
                for diagnosis in diagnoses
            ],
        }

    def format_text(
        self,
        bundle: EvidenceBundle,
        diagnoses: list[BlockerDiagnosis],
    ) -> str:
        """Create a concise investigation report."""

        lines = [
            f"Gitlexa Investigation: {bundle.repository}",
            f"Evidence collected: {len(bundle.evidence)}",
            "",
        ]

        if not diagnoses:
            lines.append("No confirmed blocker detected.")
            return "\n".join(lines)

        lines.append("BLOCKERS")

        for index, diagnosis in enumerate(diagnoses, start=1):
            lines.extend(
                [
                    "",
                    f"{index}. {diagnosis.blocker}",
                    f"Confidence: {diagnosis.confidence:.0%}",
                    f"Explanation: {diagnosis.explanation}",
                    f"Evidence: {', '.join(diagnosis.evidence_ids)}",
                    "Recommended actions:",
                ]
            )

            for action in diagnosis.recommended_actions:
                lines.append(f"- {action}")

        return "\n".join(lines)

    def format_voice(
        self,
        diagnoses: list[BlockerDiagnosis],
    ) -> str:
        """Create a short voice-friendly summary."""

        if not diagnoses:
            return "No confirmed project blocker was detected."

        diagnosis = diagnoses[0]

        return (
            f"Gitlexa detected a likely blocker: "
            f"{diagnosis.blocker}. "
            f"Confidence is {diagnosis.confidence:.0%}. "
            f"{diagnosis.explanation}"
        )# Formatter for UI and Alexa speech
