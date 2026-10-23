"""GitHub Workflows / Actions API wrapper.

Owned by Member 02 (Agent + AI + Orchestration) / GitHub Integration.
Fetches GitHub Actions workflow runs, job statuses, and failing steps.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.github.client import GitHubClient


class GitHubWorkflows:
    """Wrapper for GitHub Actions Workflow Runs REST API."""

    def __init__(self, client: Optional[GitHubClient] = None) -> None:
        self.client = client or GitHubClient()

    async def get_ci_summary(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        sha: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch latest workflow runs and diagnose any blockers/failures."""
        params: Dict[str, Any] = {"per_page": 5}
        if branch:
            params["branch"] = branch
        if sha:
            params["head_sha"] = sha

        endpoint = f"/repos/{owner}/{repo}/actions/runs"
        response = await self.client.get(endpoint, params=params)
        data = response.json()

        workflow_runs: List[Dict[str, Any]] = data.get("workflow_runs", []) if isinstance(data, dict) else []
        if not workflow_runs:
            return {
                "repository": f"{owner}/{repo}",
                "run_id": None,
                "has_blockers": False,
                "total_failed_jobs": 0,
                "failed_jobs": [],
            }

        latest_run = workflow_runs[0]
        run_id = latest_run.get("id")
        conclusion = latest_run.get("conclusion")
        status = latest_run.get("status")

        failed_jobs: List[Dict[str, Any]] = []
        if run_id is not None:
            jobs_endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
            try:
                jobs_resp = await self.client.get(jobs_endpoint)
                jobs_data = jobs_resp.json()
                all_jobs = jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else []
                for job in all_jobs:
                    if not isinstance(job, dict):
                        continue
                    job_conclusion = job.get("conclusion")
                    if job_conclusion in {"failure", "timed_out", "action_required", "cancelled"} or (
                        job_conclusion is not None and job_conclusion != "success"
                    ):
                        raw_steps = job.get("steps", [])
                        steps_list = raw_steps if isinstance(raw_steps, list) else []
                        failed_steps = [
                            step
                            for step in steps_list
                            if isinstance(step, dict)
                            and (
                                step.get("conclusion") in {"failure", "timed_out", "action_required", "cancelled"}
                                or (step.get("conclusion") is not None and step.get("conclusion") != "success")
                            )
                        ]
                        failed_jobs.append(
                            {
                                "id": job.get("id"),
                                "name": job.get("name"),
                                "conclusion": job_conclusion,
                                "status": job.get("status"),
                                "failed_steps": failed_steps,
                            }
                        )
            except Exception:
                pass

        has_blockers = (conclusion in {"failure", "timed_out", "cancelled"}) or (len(failed_jobs) > 0)

        return {
            "repository": f"{owner}/{repo}",
            "run_id": run_id,
            "workflow_name": latest_run.get("name"),
            "status": status,
            "conclusion": conclusion,
            "html_url": latest_run.get("html_url"),
            "has_blockers": has_blockers,
            "total_failed_jobs": len(failed_jobs),
            "failed_jobs": failed_jobs,
        }
