
"""Decision engine for Gitlexa's repository investigation agent."""


class DecisionEngine:
    """Evaluate evidence and determine the next investigation action."""

    def evaluate(self, evidence: list) -> str:
        """Return a recommended action based on repository evidence."""

        if not evidence:
            return (
                "INSUFFICIENT_EVIDENCE: Collect repository evidence "
                "before making a decision."
            )

        failed_ci = []
        open_prs = []
        blockers = []

        for item in evidence:
            if isinstance(item, dict):
                title = str(item.get("title", "")).lower()
                status = str(
                    item.get("status")
                    or item.get("conclusion")
                    or item.get("state")
                    or ""
                ).lower()
            else:
                title = str(getattr(item, "title", "")).lower()
                metadata = getattr(item, "metadata", {}) or {}
                status = str(
                    metadata.get("status")
                    or metadata.get("conclusion")
                    or metadata.get("state")
                    or getattr(item, "status", "")
                    or ""
                ).lower()

            if status in {
                "failure", "failed", "error", "timed_out", "cancelled"
            }:
                if any(word in title for word in (
                     "ci", "pipeline", "workflow", "test", "build", "check"
                )):
                    failed_ci.append(title)
                else:
                    blockers.append(title)

            if "pull request" in title or "pr #" in title:
                open_prs.append(title)

            if any(word in title for word in (
                "blocker", "authentication", "unauthorized"
            )):
                blockers.append(title)

        if failed_ci:
            return (
                "INVESTIGATE_CI_FAILURE: Inspect failed CI logs, "
                "identify the first failing step, and correlate "
                "the failure with recent code changes."
            )

        if blockers:
            return (
                "INVESTIGATE_BLOCKER: Validate the reported blocker "
                "against supporting evidence and relevant code."
            )

        if open_prs:
            return (
                "INVESTIGATE_PULL_REQUEST: Inspect PR details, "
                "review status checks, and identify unresolved checks."
            )

        return (
            "GATHER_MORE_EVIDENCE: Inspect recent commits, pull requests, "
            "CI runs, and related code before deciding."
        )

