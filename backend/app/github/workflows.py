"""GitHub Actions and CI intelligence wrapper for Gitlexa.

Owned by Member 03 (GitHub Integration & Repository Intelligence).
Provides structured methods to inspect GitHub Actions workflow runs,
retrieve job details, isolate failed steps, fetch failure logs safely,
and query commit statuses and check runs for the Evidence Engine.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional

from app.core.exceptions import (
    GitHubIntegrationError,
    ResourceNotFoundError,
)
from app.core.logging import logger
from app.github.client import GitHubClient


class GitHubWorkflows:
    """High-level GitHub Actions & CI intelligence API wrapper."""

    FAILED_CONCLUSIONS = {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}

    def __init__(self, client: Optional[GitHubClient] = None) -> None:
        """Initialize with an existing or new GitHubClient instance."""
        self.client: GitHubClient = client or GitHubClient()

    async def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        status: Optional[str] = None,
        event: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """List workflow runs for a repository with optional filtering.

        Args:
            owner: Repository owner/organization.
            repo: Repository name.
            branch: Filter by Git branch name.
            status: Filter by status (e.g. 'completed', 'in_progress', 'failure').
            event: Filter by triggering event (e.g. 'push', 'pull_request').
            per_page: Results per page (max 100).
            page: Page number to fetch.

        Returns:
            List of workflow run dictionaries.
        """
        params: Dict[str, Any] = {"per_page": per_page, "page": page}
        if branch:
            params["branch"] = branch
        if status:
            params["status"] = status
        if event:
            params["event"] = event

        endpoint = f"/repos/{owner}/{repo}/actions/runs"
        data = await self.client.get(endpoint, params=params)

        if isinstance(data, dict):
            return data.get("workflow_runs", [])
        return []

    async def paginate_workflow_runs(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        status: Optional[str] = None,
        event: Optional[str] = None,
        max_pages: Optional[int] = None,
        per_page: int = 30,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Asynchronously yield workflow runs across paginated results.

        Args:
            owner: Repository owner.
            repo: Repository name.
            branch: Optional branch filter.
            status: Optional status filter.
            event: Optional event filter.
            max_pages: Maximum pages to traverse.
            per_page: Items per page.

        Yields:
            Individual workflow run dictionaries.
        """
        params: Dict[str, Any] = {"per_page": per_page}
        if branch:
            params["branch"] = branch
        if status:
            params["status"] = status
        if event:
            params["event"] = event

        endpoint = f"/repos/{owner}/{repo}/actions/runs"
        async for page in self.client.paginate_pages(endpoint, params=params, max_pages=max_pages, per_page=per_page):
            # If the response is a dictionary with 'workflow_runs'
            if isinstance(page, list):
                for item in page:
                    if isinstance(item, dict) and "workflow_runs" in item:
                        for run in item.get("workflow_runs", []):
                            yield run
                    else:
                        yield item

    async def get_workflow_run(self, owner: str, repo: str, run_id: int) -> Dict[str, Any]:
        """Retrieve details for a single workflow run.

        Args:
            owner: Repository owner.
            repo: Repository name.
            run_id: ID of the workflow run.

        Returns:
            Workflow run details dictionary.
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}"
        data = await self.client.get(endpoint)
        return data if isinstance(data, dict) else {}

    async def get_workflow_run_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        filter_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve jobs belonging to a workflow run.

        Args:
            owner: Repository owner.
            repo: Repository name.
            run_id: Workflow run ID.
            filter_status: Optional conclusion or status filter (e.g. 'failure').

        Returns:
            List of job dictionaries.
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
        data = await self.client.get(endpoint, params={"per_page": 100})

        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        if filter_status:
            target = filter_status.lower()
            jobs = [
                j for j in jobs
                if str(j.get("conclusion") or "").lower() == target
                or str(j.get("status") or "").lower() == target
            ]
        return jobs

    async def get_failed_jobs(self, owner: str, repo: str, run_id: int) -> List[Dict[str, Any]]:
        """Identify failed jobs and extract failing steps within them.

        Args:
            owner: Repository owner.
            repo: Repository name.
            run_id: Workflow run ID.

        Returns:
            List of failed job dictionaries with an added 'failed_steps' field.
        """
        all_jobs = await self.get_workflow_run_jobs(owner, repo, run_id)
        failed_jobs: List[Dict[str, Any]] = []

        for job in all_jobs:
            conclusion = str(job.get("conclusion") or "").lower()
            if conclusion in self.FAILED_CONCLUSIONS:
                job_copy = dict(job)
                steps = job.get("steps", [])
                failed_steps = [
                    s for s in steps
                    if str(s.get("conclusion") or "").lower() in self.FAILED_CONCLUSIONS
                ]
                job_copy["failed_steps"] = failed_steps
                failed_jobs.append(job_copy)

        return failed_jobs

    async def get_job_failure_logs(
        self,
        owner: str,
        repo: str,
        job_id: int,
        max_lines: int = 150,
    ) -> Dict[str, Any]:
        """Retrieve failure logs for a specific job where supported and permitted.

        Handles GitHub's 302 redirect for log downloads, and handles 404
        (expired logs) or 403 (insufficient permissions) gracefully.

        Args:
            owner: Repository owner.
            repo: Repository name.
            job_id: Job ID to inspect.
            max_lines: Maximum tail lines to include in the snippet.

        Returns:
            Dictionary with log availability, metadata, and extracted snippet.
        """
        endpoint = f"/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"

        try:
            resp = await self.client.request_raw("GET", endpoint)

            # GitHub returns 302 Found redirecting to a signed download URL
            if resp.status_code == 302:
                redirect_url = resp.headers.get("location")
                if redirect_url:
                    log_resp = await self.client.request_raw("GET", redirect_url)
                    raw_log = str(log_resp.data or "")
                else:
                    return {
                        "job_id": job_id,
                        "available": False,
                        "reason": "Missing redirect location header for job logs",
                        "snippet": None,
                        "total_lines": 0,
                    }
            elif resp.status_code == 200:
                raw_log = str(resp.data or "")
            else:
                return {
                    "job_id": job_id,
                    "available": False,
                    "reason": f"Unexpected status code {resp.status_code} fetching logs",
                    "snippet": None,
                    "total_lines": 0,
                }

        except ResourceNotFoundError:
            logger.info("Logs for job %d in %s/%s are unavailable or expired (404)", job_id, owner, repo)
            return {
                "job_id": job_id,
                "available": False,
                "reason": "Logs expired or not found (404)",
                "snippet": None,
                "total_lines": 0,
            }
        except GitHubIntegrationError as exc:
            if exc.status_code == 403:
                logger.warning("Access denied to logs for job %d in %s/%s (403)", job_id, owner, repo)
                return {
                    "job_id": job_id,
                    "available": False,
                    "reason": "Insufficient permissions to read job logs (403)",
                    "snippet": None,
                    "total_lines": 0,
                }
            raise

        lines = raw_log.splitlines()
        total_lines = len(lines)
        snippet_lines = lines[-max_lines:] if total_lines > max_lines else lines

        return {
            "job_id": job_id,
            "available": True,
            "total_lines": total_lines,
            "truncated": total_lines > max_lines,
            "snippet": "\n".join(snippet_lines),
        }

    async def get_commit_check_runs(
        self,
        owner: str,
        repo: str,
        ref: str,
        check_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve check runs for a commit ref (branch, tag, or SHA).

        Args:
            owner: Repository owner.
            repo: Repository name.
            ref: Commit SHA, branch, or tag.
            check_name: Optional filter by check run name.
            status: Optional filter by status ('queued', 'in_progress', 'completed').

        Returns:
            List of check run dictionaries.
        """
        endpoint = f"/repos/{owner}/{repo}/commits/{ref}/check-runs"
        params: Dict[str, Any] = {"per_page": 100}
        if check_name:
            params["check_name"] = check_name
        if status:
            params["status"] = status

        data = await self.client.get(endpoint, params=params)
        if isinstance(data, dict):
            return data.get("check_runs", [])
        return []

    async def get_commit_status(self, owner: str, repo: str, ref: str) -> Dict[str, Any]:
        """Retrieve the combined commit status for a ref.

        Args:
            owner: Repository owner.
            repo: Repository name.
            ref: Commit SHA, branch, or tag.

        Returns:
            Combined status dictionary including 'state', 'statuses', and 'total_count'.
        """
        endpoint = f"/repos/{owner}/{repo}/commits/{ref}/status"
        data = await self.client.get(endpoint)
        return data if isinstance(data, dict) else {}

    async def get_ci_summary(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        sha: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate high-level CI intelligence summary for Evidence Engine and MCP.

        Combines latest workflow run, execution status, failed jobs, and failing steps.

        Args:
            owner: Repository owner.
            repo: Repository name.
            branch: Git branch name.
            sha: Optional commit SHA.

        Returns:
            Structured CI summary dictionary.
        """
        runs = await self.list_workflow_runs(owner, repo, branch=branch, per_page=1)
        latest_run = runs[0] if runs else None

        failed_jobs: List[Dict[str, Any]] = []
        is_failing = False

        if latest_run:
            conclusion = str(latest_run.get("conclusion") or "").lower()
            status = str(latest_run.get("status") or "").lower()
            is_failing = conclusion in self.FAILED_CONCLUSIONS

            if is_failing:
                failed_jobs = await self.get_failed_jobs(owner, repo, latest_run["id"])

        ref = sha or (latest_run.get("head_sha") if latest_run else branch or "HEAD")

        return {
            "repository": f"{owner}/{repo}",
            "branch": branch,
            "sha": ref,
            "run_id": latest_run.get("id") if latest_run else None,
            "workflow_name": latest_run.get("name") if latest_run else None,
            "status": latest_run.get("status") if latest_run else "unknown",
            "conclusion": latest_run.get("conclusion") if latest_run else None,
            "html_url": latest_run.get("html_url") if latest_run else None,
            "has_blockers": is_failing,
            "failed_jobs": failed_jobs,
            "total_failed_jobs": len(failed_jobs),
        }
