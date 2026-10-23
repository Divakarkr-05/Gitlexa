"""MCP Tool: get_recovery_plan.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Generates read-only, evidence-grounded recovery recommendations based on blocker diagnosis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.exceptions import GitlexaException, MCPToolExecutionError
from app.core.logging import logger
from app.github.client import GitHubClient
from app.mcp.tools.get_blocker_diagnosis import get_blocker_diagnosis
from app.mcp.tools.investigate_repository import resolve_owner_repo


async def get_recovery_plan(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    client: Optional[GitHubClient] = None,
) -> Dict[str, Any]:
    """Generate a step-by-step read-only recovery plan based strictly on evidence.

    Args:
        owner: Repository owner/org.
        repo: Repository name.
        client: Optional pre-configured GitHubClient.

    Returns:
        Structured dictionary containing a list of numbered recovery steps,
        each with an action, rationale, and supporting evidence reference.
    """
    clean_owner, clean_repo = resolve_owner_repo(owner=owner, repo=repo)
    full_repo_name = f"{clean_owner}/{clean_repo}"

    try:
        diagnosis = await get_blocker_diagnosis(
            owner=clean_owner,
            repo=clean_repo,
            client=client,
        )

        steps: List[Dict[str, Any]] = []

        if not diagnosis.get("blocked"):
            # Repository is healthy, no recovery actions needed
            steps.append({
                "step": 1,
                "action": "Continue active development and maintenance.",
                "reason": "No active blockers or failing CI pipelines were detected.",
                "evidence": "Telemetry verification confirmed clean workflow and issue states.",
            })
            return {"steps": steps}

        # Blocker detected: generate targeted read-only recovery recommendations
        blocker_name = diagnosis.get("blocker", "Pipeline Blocker")
        explanation = diagnosis.get("explanation", "")
        evidence_items = diagnosis.get("evidence", [])

        primary_evidence = evidence_items[0] if evidence_items else {}
        evidence_ref = (
            primary_evidence.get("source_url")
            or primary_evidence.get("title")
            or f"{full_repo_name} pipeline telemetry"
        )

        steps.append({
            "step": 1,
            "action": "Inspect failed CI run logs and extract error stack trace.",
            "reason": f"Investigate root cause of '{blocker_name}': {explanation}",
            "evidence": str(evidence_ref),
        })
        steps.append({
            "step": 2,
            "action": "Review recent commit modifications correlating with the failure timestamp.",
            "reason": "Isolate the specific file or diff hunk introducing the syntax, type, or test regression.",
            "evidence": "Correlated commit delta",
        })
        steps.append({
            "step": 3,
            "action": "Reproduce and diagnose the failure locally using local test and lint runners.",
            "reason": "Confirm root cause in an isolated local environment prior to proposing changes.",
            "evidence": "Local verification environment",
        })
        steps.append({
            "step": 4,
            "action": "Draft and review the minimal necessary corrective change.",
            "reason": "Remediate the blocker with minimal collateral change.",
            "evidence": "Targeted fix review",
        })
        steps.append({
            "step": 5,
            "action": "Push the validated fix and verify GitHub Actions CI concludes with success.",
            "reason": "Confirm complete resolution and restoration of pipeline health.",
            "evidence": "GitHub Actions workflow status check",
        })

        return {"steps": steps}

    except GitlexaException:
        raise
    except Exception as exc:
        logger.error("Failed to generate recovery plan for %s: %s", full_repo_name, exc)
        raise MCPToolExecutionError(
            tool_name="get_recovery_plan",
            message=str(exc),
            details={"repository": full_repo_name},
        ) from exc
