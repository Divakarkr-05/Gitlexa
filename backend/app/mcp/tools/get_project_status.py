"""MCP Tool: get_project_status.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Evaluates repository evidence to determine project status: healthy, warning, blocked, or unknown.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.exceptions import GitlexaException, MCPToolExecutionError
from app.core.logging import logger
from app.github.client import GitHubClient
from app.mcp.tools.investigate_repository import investigate_repository, resolve_owner_repo


async def get_project_status(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    client: Optional[GitHubClient] = None,
) -> Dict[str, Any]:
    """Determine repository project health status based on actual GitHub evidence.

    Args:
        owner: Repository owner/org.
        repo: Repository name.
        client: Optional pre-configured GitHubClient.

    Returns:
        Structured dictionary with repository, status ('healthy', 'warning', 'blocked', 'unknown'),
        evidence-based reason, and supporting evidence items.
    """
    clean_owner, clean_repo = resolve_owner_repo(owner=owner, repo=repo)
    full_repo_name = f"{clean_owner}/{clean_repo}"

    try:
        investigation = await investigate_repository(
            owner=clean_owner,
            repo=clean_repo,
            client=client,
        )

        ci_status: List[Dict[str, Any]] = investigation.get("ci_status", [])
        pull_requests: List[Dict[str, Any]] = investigation.get("pull_requests", [])
        commits: List[Dict[str, Any]] = investigation.get("commits", [])
        issues: List[Dict[str, Any]] = investigation.get("issues", [])

        evidence_items: List[Dict[str, Any]] = []

        # 1. Check for CI failures (Blocker condition)
        has_failed_ci = False
        failing_run_name = ""
        for ci in ci_status:
            if ci.get("has_blockers") or ci.get("conclusion") in ("failure", "timed_out", "cancelled"):
                has_failed_ci = True
                failing_run_name = str(ci.get("workflow_name") or ci.get("name") or "CI Workflow")
                evidence_items.append({
                    "type": "ci_run",
                    "id": str(ci.get("run_id") or ci.get("id")),
                    "title": failing_run_name,
                    "status": ci.get("conclusion") or ci.get("status"),
                    "url": ci.get("html_url"),
                })

        if has_failed_ci:
            return {
                "repository": full_repo_name,
                "status": "blocked",
                "reason": f"Active CI blocker detected: '{failing_run_name}' pipeline execution failed.",
                "evidence": evidence_items,
            }

        # 2. Check for merge conflicts or PR review issues (Warning condition)
        has_warnings = False
        warning_reasons: List[str] = []
        for pr in pull_requests:
            if pr.get("mergeable") is False:
                has_warnings = True
                warning_reasons.append(f"PR #{pr.get('number')} has unresolved merge conflicts")
                evidence_items.append({
                    "type": "pull_request",
                    "id": str(pr.get("number")),
                    "title": str(pr.get("title")),
                    "status": "merge_conflict",
                })

        if has_warnings:
            return {
                "repository": full_repo_name,
                "status": "warning",
                "reason": "; ".join(warning_reasons),
                "evidence": evidence_items,
            }

        # 3. Healthy condition
        if ci_status or commits or pull_requests or issues:
            successful_runs = [
                ci for ci in ci_status
                if ci.get("conclusion") == "success" or ci.get("status") == "completed"
            ]
            for run in successful_runs[:3]:
                evidence_items.append({
                    "type": "ci_run",
                    "id": str(run.get("run_id") or run.get("id")),
                    "title": str(run.get("workflow_name") or run.get("name") or "CI"),
                    "status": "success",
                })

            return {
                "repository": full_repo_name,
                "status": "healthy",
                "reason": "All recent workflow runs and checks succeeded with no active blockers.",
                "evidence": evidence_items,
            }

        # 4. Unknown condition (no telemetry could be fetched)
        return {
            "repository": full_repo_name,
            "status": "unknown",
            "reason": "No recent telemetry or workflow signals were found for this repository.",
            "evidence": [],
        }

    except GitlexaException:
        raise
    except Exception as exc:
        logger.error("Failed to determine project status for %s: %s", full_repo_name, exc)
        raise MCPToolExecutionError(
            tool_name="get_project_status",
            message=str(exc),
            details={"repository": full_repo_name},
        ) from exc
