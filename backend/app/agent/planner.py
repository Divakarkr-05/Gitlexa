
"""Task planner for Gitlexa's repository investigation agent."""


class AgentPlanner:
    """Convert a user goal into an ordered investigation plan."""

    def plan(self, goal: str) -> list[str]:
        """Generate investigation steps based on the user's goal."""

        if not goal or not goal.strip():
            return ["Ask the user to provide a repository investigation goal."]

        text = goal.lower()
        steps: list[str] = []

        def matches(*keywords: str) -> bool:
            return any(keyword in text for keyword in keywords)

        # Identify pull requests and CI failures.
        if matches(
            "pull request", "pr #", "pull-request",
            "merge request", "ci", "pipeline", "build failure",
            "failing test", "failed test", "workflow",
        ):
            steps.extend([
                "Retrieve the relevant pull request and CI status.",
                "Inspect failed checks and available execution logs.",
                "Collect related code changes and repository evidence.",
                "Correlate the failure with relevant evidence.",
            ])

        # Identify issues and project blockers.
        if matches(
            "issue", "bug", "blocker", "blocked",
            "root cause", "problem", "error", "failure",
        ):
            steps.extend([
                "Retrieve relevant issues and blocker information.",
                "Analyze evidence to identify likely root causes.",
                "Separate confirmed findings from possible explanations.",
            ])

        # Identify code-focused investigations.
        if matches(
            "code", "function", "file", "implementation",
            "commit", "search", "authentication", "token",
        ):
            steps.extend([
                "Search relevant source code and recent changes.",
                "Connect code findings to the reported problem.",
            ])

        # Identify repository health and general analysis requests.
        if matches(
            "repository", "repo", "project health",
            "overall health", "summary", "analyze", "analyse",
        ):
            steps.extend([
                "Inspect repository health and recent activity.",
                "Identify significant risks and unresolved blockers.",
            ])

        # Safe default for requests that do not match a category.
        if not steps:
            steps.extend([
                "Identify the repository context and investigation goal.",
                "Retrieve relevant GitHub information and available evidence.",
                "Evaluate findings and determine the next useful action.",
            ])

        # Preserve order while removing duplicate steps.
        return list(dict.fromkeys(steps))

