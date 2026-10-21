"""Correlate related evidence across issues, PRs, CI, commits, and logs."""

from app.evidence.schemas import Correlation, EvidenceBundle


class EvidenceCorrelator:
    """Find relationships between evidence items."""

    def correlate(self, bundle: EvidenceBundle) -> list[Correlation]:
        correlations: list[Correlation] = []

        for index, first in enumerate(bundle.evidence):
            for second in bundle.evidence[index + 1 :]:
                relationship = self._find_relationship(first, second)

                if relationship is None:
                    continue

                correlations.append(
                    Correlation(
                        id=f"correlation-{len(correlations) + 1}",
                        evidence_ids=[first.id, second.id],
                        relationship=relationship,
                        explanation=self._explanation(
                            first.type.value,
                            second.type.value,
                            relationship,
                        ),
                        confidence=0.85,
                    )
                )

        return correlations

    @staticmethod
    def _find_relationship(first, second) -> str | None:
        first_type = first.type.value
        second_type = second.type.value

        pair = {first_type, second_type}

        if pair == {"pull_request", "ci_run"}:
            return "pr_ci"

        if pair == {"issue", "pull_request"}:
            return "issue_pr"

        if pair == {"pull_request", "commit"}:
            return "pr_commit"

        if pair == {"commit", "ci_run"}:
            return "commit_ci"

        if pair == {"ci_run", "log"}:
            return "ci_log"

        if pair == {"issue", "commit"}:
            return "issue_commit"

        if pair == {"code", "ci_run"}:
            return "code_ci"

        return None

    @staticmethod
    def _explanation(
        first_type: str,
        second_type: str,
        relationship: str,
    ) -> str:
        explanations = {
            "pr_ci": "A pull request is associated with a CI execution.",
            "issue_pr": "A pull request may address or relate to an issue.",
            "pr_commit": "A commit is associated with changes in a pull request.",
            "commit_ci": "A CI execution is associated with a commit.",
            "ci_log": "Logs provide diagnostic evidence for a CI execution.",
            "issue_commit": "A commit may contain changes related to an issue.",
            "code_ci": "Code findings may explain a CI failure.",
        }

        return explanations.get(
            relationship,
            f"{first_type} and {second_type} are related.",
        )# Correlation engine linking PRs, CI, and Issues
