"""Demo script demonstrating the complete Gitlexa investigation chain.

Executes:
1. investigate_repository(owner="Divakarkr-05", repo="Gitlexa")
2. get_project_status(owner="Divakarkr-05", repo="Gitlexa")
3. get_blocker_diagnosis(owner="Divakarkr-05", repo="Gitlexa")
4. get_recovery_plan(owner="Divakarkr-05", repo="Gitlexa")

Run via:
    cd backend
    python -m app.mcp.demo
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Dict

from app.mcp import (
    get_blocker_diagnosis,
    get_project_status,
    get_recovery_plan,
    investigate_repository,
)


def _print_step(step_number: int, title: str, data: Dict[str, Any]) -> None:
    """Print formatted step header and machine-readable JSON output."""
    separator = "=" * 60
    print(f"\n{separator}")
    print(f"STEP {step_number}: {title}")
    print(separator)
    print(json.dumps(data, indent=2, default=str))


async def run_investigation_demo(
    owner: str = "Divakarkr-05",
    repo: str = "Gitlexa",
) -> Dict[str, Any]:
    """Execute the end-to-end Gitlexa investigation chain and return aggregated output."""
    print(f"Running Gitlexa Investigation Chain for: {owner}/{repo}")

    # 1. Investigate repository (gather raw telemetry and build evidence bundle)
    investigation = await investigate_repository(owner=owner, repo=repo)
    _print_step(
        1,
        "investigate_repository",
        {
            "repository": investigation["repository"],
            "issues_count": len(investigation["issues"]),
            "pull_requests_count": len(investigation["pull_requests"]),
            "commits_count": len(investigation["commits"]),
            "ci_status_count": len(investigation["ci_status"]),
            "evidence_count": investigation["evidence_count"],
        },
    )

    # 2. Get project status (healthy, warning, blocked, unknown)
    project_status = await get_project_status(owner=owner, repo=repo)
    _print_step(2, "get_project_status", project_status)

    # 3. Get blocker diagnosis (evidence-grounded diagnosis + confidence)
    diagnosis = await get_blocker_diagnosis(owner=owner, repo=repo)
    _print_step(3, "get_blocker_diagnosis", diagnosis)

    # 4. Get recovery plan (read-only recommended steps)
    recovery_plan = await get_recovery_plan(owner=owner, repo=repo)
    _print_step(4, "get_recovery_plan", recovery_plan)

    return {
        "repository": f"{owner}/{repo}",
        "investigation_summary": {
            "evidence_count": investigation["evidence_count"],
        },
        "status": project_status["status"],
        "blocked": diagnosis["blocked"],
        "plan_steps_count": len(recovery_plan["steps"]),
    }


def main() -> None:
    owner = sys.argv[1] if len(sys.argv) > 1 else "Divakarkr-05"
    repo = sys.argv[2] if len(sys.argv) > 2 else "Gitlexa"
    asyncio.run(run_investigation_demo(owner=owner, repo=repo))


if __name__ == "__main__":
    main()
