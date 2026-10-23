
"""Orchestrator for Gitlexa's repository investigation agent."""

from app.agent.planner import AgentPlanner
from app.agent.decision import DecisionEngine


class AgentOrchestrator:
    """Coordinate planning, evidence evaluation, and recommendations."""

    def __init__(self):
        self.planner = AgentPlanner()
        self.decision_engine = DecisionEngine()

    @staticmethod
    def _get_finding(item) -> dict:
        """Safely normalize evidence into a finding dictionary."""

        if isinstance(item, dict):
            return {
                "title": str(item.get("title") or "Evidence"),
                "status": str(
                    item.get("status")
                    or item.get("conclusion")
                    or item.get("state")
                    or "unknown"
                ),
            }

        metadata = getattr(item, "metadata", None)
        if not isinstance(metadata, dict):
            metadata = {}

        return {
            "title": str(getattr(item, "title", None) or "Evidence"),
            "status": str(
                metadata.get("status")
                or metadata.get("conclusion")
                or metadata.get("state")
                or getattr(item, "status", None)
                or "unknown"
            ),
        }

    async def execute_query(
        self,
        user_prompt: str,
        evidence: list | None = None,
    ) -> dict:
        """Plan an investigation and evaluate any supplied evidence."""

        if not user_prompt or not user_prompt.strip():
            return {
                "status": "needs_input",
                "query": user_prompt or "",
                "plan": ["Provide a repository investigation goal."],
                "decision": "INSUFFICIENT_EVIDENCE",
                "findings": [],
                "message": "Please describe what Gitlexa should investigate.",
            }

        plan = self.planner.plan(user_prompt)
        evidence = evidence or []
        decision = self.decision_engine.evaluate(evidence)

        return {
            "status": "analyzed" if evidence else "planned",
            "query": user_prompt,
            "plan": plan,
            "decision": decision,
            "findings": [
                self._get_finding(item)
                for item in evidence
            ],
            "message": (
                "Decision generated from supplied evidence. "
                "Validate the evidence before treating a likely cause as confirmed."
                if evidence
                else "Investigation plan generated. Repository evidence is still needed."
            ),
        }
