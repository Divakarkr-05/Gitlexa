"""MCP Tool: get_blocker_diagnosis.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Reuses the Evidence Engine and BlockerDetector to evaluate correlated evidence
and produce an evidence-grounded blocker diagnosis.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.exceptions import GitlexaException, MCPToolExecutionError
from app.core.logging import logger
from app.evidence.blocker_detection import BlockerDetector
from app.evidence.correlation import EvidenceCorrelator
from app.evidence.github_adapter import GitHubEvidenceAdapter
from app.github.client import GitHubClient
from app.mcp.tools.investigate_repository import investigate_repository, resolve_owner_repo


async def get_blocker_diagnosis(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    client: Optional[GitHubClient] = None,
) -> Dict[str, Any]:
    """Diagnose repository blockers using the Evidence Engine.

    Args:
        owner: Repository owner/org.
        repo: Repository name.
        client: Optional pre-configured GitHubClient.

    Returns:
        Structured dictionary with blocked boolean, blocker description,
        confidence score (0.0 to 1.0), and supporting evidence list.
    """
    clean_owner, clean_repo = resolve_owner_repo(owner=owner, repo=repo)
    full_repo_name = f"{clean_owner}/{clean_repo}"

    try:
        investigation = await investigate_repository(
            owner=clean_owner,
            repo=clean_repo,
            client=client,
        )

        raw_issues = investigation.get("issues", [])
        raw_prs = investigation.get("pull_requests", [])
        raw_ci = investigation.get("ci_status", [])
        raw_commits = investigation.get("commits", [])

        # 1. Collect normalized evidence bundle
        adapter = GitHubEvidenceAdapter()
        bundle = adapter.collect(
            repository=full_repo_name,
            issues=raw_issues,
            pull_requests=raw_prs,
            ci_runs=raw_ci,
            commits=raw_commits,
        )

        # 2. Correlate evidence across signals
        correlator = EvidenceCorrelator()
        correlations = correlator.correlate(bundle)

        # 3. Detect blockers using BlockerDetector
        detector = BlockerDetector()
        diagnoses = detector.detect(bundle, correlations)

        if not diagnoses:
            return {
                "blocked": False,
                "blocker": "No blocker detected in repository telemetry.",
                "confidence": 0.0,
                "evidence": [],
            }

        primary_diagnosis = diagnoses[0]
        confidence = max(0.0, min(1.0, float(primary_diagnosis.confidence)))

        # Extract only the supporting evidence items
        supporting_evidence: List[Dict[str, Any]] = [
            item.model_dump()
            for item in bundle.evidence
            if item.id in primary_diagnosis.evidence_ids
        ]

        return {
            "blocked": True,
            "blocker": primary_diagnosis.blocker,
            "confidence": round(confidence, 2),
            "explanation": primary_diagnosis.explanation,
            "evidence": supporting_evidence,
        }

    except GitlexaException:
        raise
    except Exception as exc:
        logger.error("Failed to diagnose blockers for %s: %s", full_repo_name, exc)
        raise MCPToolExecutionError(
            tool_name="get_blocker_diagnosis",
            message=str(exc),
            details={"repository": full_repo_name},
        ) from exc
