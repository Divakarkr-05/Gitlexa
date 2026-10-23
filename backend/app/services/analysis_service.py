"""Synchronous analysis orchestration for demo and live repository analysis."""

import re
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.evidence.blocker_detection import BlockerDetector
from app.evidence.github_adapter import GitHubEvidenceAdapter
from app.evidence.schemas import Evidence
from app.evidence.scoring import EvidenceScorer
from app.schemas.analysis import (
    AnalysisResponse,
    BlockerResult,
    EvidenceResult,
    RepositoryMetadata,
)
from app.schemas.project import ProjectResponse


GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
GITHUB_PAGE_SIZE = 100
GITHUB_MAX_PAGES = 10


class GitHubAnalysisError(Exception):
    """Safe upstream error to translate into an HTTP response."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class AnalysisService:
    """Run demo fixtures or live GitHub observations through the evidence pipeline."""

    def run_demo(self, project: ProjectResponse, analysis_id: UUID) -> AnalysisResponse:
        parsed_url = urlsplit(project.repo_url)
        repository = parsed_url.path.strip("/").removesuffix(".git")
        bundle = GitHubEvidenceAdapter().collect(
            repository,
            ci_runs=[
                {
                    "id": "demo-ci-1",
                    "name": "DEMO/SIMULATED test workflow",
                    "description": (
                        "DEMO/SIMULATED fixture status: failure. This data was not "
                        "retrieved from the registered repository or GitHub."
                    ),
                    "status": "failure",
                }
            ],
        )

        diagnoses = BlockerDetector().detect(bundle, [])
        scores = {
            score.evidence_id: score
            for score in (
                EvidenceScorer().score(item) for item in bundle.evidence
            )
        }
        evidence = [
            EvidenceResult(
                id=item.id,
                type=item.type,
                title=f"DEMO/SIMULATED: {item.title}",
                description=item.description,
                source_url=None,
                source_ref=None,
                timestamp=item.timestamp,
                score=scores[item.id].overall_score,
                simulated=True,
            )
            for item in bundle.evidence
        ]
        blockers = [
            BlockerResult(
                id=f"demo-blocker-{index}",
                title=f"DEMO/SIMULATED: {diagnosis.blocker}",
                explanation=(
                    "DEMO/SIMULATED fixture only; this is not a finding about the "
                    "registered repository. "
                    f"{diagnosis.explanation}"
                ),
                impact=(
                    "DEMO scenario only: if a real required test workflow failed, "
                    "it could block a release until corrected."
                ),
                severity="high",
                confidence=diagnosis.confidence,
                evidence_ids=diagnosis.evidence_ids,
                recommended_actions=[
                    "DEMO/SIMULATED: This fixture has no real run or logs. For a real "
                    "investigation, inspect the repository's CI provider and first "
                    "failing step."
                ],
            )
            for index, diagnosis in enumerate(diagnoses, start=1)
        ]

        return AnalysisResponse(
            analysis_id=analysis_id,
            project_id=UUID(project.id),
            repository=repository,
            status="completed",
            source="demo",
            simulated=True,
            analyzed_at=datetime.now(timezone.utc),
            repository_metadata=None,
            data_availability={
                "repository": "not fetched in demo mode",
                "issues": "not fetched in demo mode",
                "pull_requests": "not fetched in demo mode",
                "commits": "not fetched in demo mode",
                "workflow_runs": "not fetched in demo mode",
            },
            summary=(
                "DEMO/SIMULATED: A fixed failed-CI scenario was analyzed. No data was "
                "retrieved from or verified against the registered GitHub repository."
            ),
            blockers=blockers,
            evidence=evidence,
            correlations=[],
        )

    async def run_live(
        self,
        project: ProjectResponse,
        analysis_id: UUID,
    ) -> AnalysisResponse:
        owner, repository = self._repository_coordinates(project.repo_url)
        token = settings.get_github_token_value()
        if not token:
            from app.github.app_auth import github_app_auth
            if github_app_auth.is_configured:
                try:
                    token = await github_app_auth.get_installation_token()
                except Exception as exc:
                    logger.debug("Could not resolve GitHub App token for analysis: %s", exc)

        headers = dict(GITHUB_API_HEADERS)
        if token and token.strip():
            headers["Authorization"] = "Bearer " + token.strip()

        timeout = httpx.Timeout(15.0, connect=5.0)
        async with httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
            follow_redirects=False,
        ) as client:
            metadata_payload = await self._get_json(
                client,
                f"{GITHUB_API_BASE}/repos/{owner}/{repository}",
                required=True,
            )
            if not isinstance(metadata_payload, dict):
                raise GitHubAnalysisError(502, "GitHub returned invalid repository metadata.")
            metadata = self._repository_metadata(metadata_payload)
            repository_name = str(metadata_payload["full_name"])
            availability: dict[str, str] = {
                "repository": "available",
            }
            issue_records: list[dict] = []
            pull_records: list[dict] = []
            commit_records: list[dict] = []
            workflow_records: list[dict] = []
            resources = (
                ("issues", f"{GITHUB_API_BASE}/repos/{owner}/{repository}/issues?state=open", issue_records),
                ("pull_requests", f"{GITHUB_API_BASE}/repos/{owner}/{repository}/pulls?state=open", pull_records),
                ("commits", f"{GITHUB_API_BASE}/repos/{owner}/{repository}/commits", commit_records),
                ("workflow_runs", f"{GITHUB_API_BASE}/repos/{owner}/{repository}/actions/runs", workflow_records),
            )
            for name, url, destination in resources:
                records, status = await self._get_paginated(client, url)
                availability[name] = status
                destination.extend(records)

        issues = [
            self._issue_record(item)
            for item in issue_records
            if "pull_request" not in item
        ]
        pull_requests = [self._pull_request_record(item) for item in pull_records]
        commits = [self._commit_record(item) for item in commit_records]
        workflow_runs = [
            self._workflow_record(item)
            for item in workflow_records
        ]
        bundle = GitHubEvidenceAdapter().collect(
            repository_name,
            issues=issues,
            pull_requests=pull_requests,
            commits=commits,
            ci_runs=workflow_runs,
        )
        diagnoses = BlockerDetector().detect(bundle, [])
        score_by_id = {
            score.evidence_id: score
            for score in (
                EvidenceScorer().score(item) for item in bundle.evidence
            )
        }
        evidence = [
            EvidenceResult(
                id=item.id,
                type=item.type,
                title=item.title,
                description=item.description,
                source_url=item.source_url,
                source_ref=item.source_ref,
                timestamp=item.timestamp,
                score=score_by_id[item.id].overall_score,
                simulated=False,
            )
            for item in bundle.evidence
        ]
        evidence_by_id = {item.id: item for item in bundle.evidence}
        blockers = [
            self._live_blocker(index, diagnosis, evidence_by_id)
            for index, diagnosis in enumerate(diagnoses, start=1)
        ]
        summary = self._live_summary(repository_name, metadata_payload, availability, blockers)

        return AnalysisResponse(
            analysis_id=analysis_id,
            project_id=UUID(project.id),
            repository=repository_name,
            status="completed",
            source="live",
            simulated=False,
            analyzed_at=datetime.now(timezone.utc),
            repository_metadata=metadata,
            data_availability=availability,
            summary=summary,
            blockers=blockers,
            evidence=evidence,
            correlations=[],
        )

    @staticmethod
    def _repository_coordinates(repo_url: str) -> tuple[str, str]:
        parsed_url = urlsplit(repo_url)
        if (
            parsed_url.scheme.lower() != "https"
            or parsed_url.hostname is None
            or parsed_url.hostname.lower() != "github.com"
            or parsed_url.username is not None
            or parsed_url.password is not None
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise GitHubAnalysisError(
                400,
                "The registered URL is not a valid HTTPS github.com repository URL.",
            )

        parts = parsed_url.path.strip("/").split("/")
        if len(parts) != 2:
            raise GitHubAnalysisError(
                400,
                "The registered URL must contain a GitHub owner and repository name.",
            )
        owner, repository = parts
        repository = repository.removesuffix(".git")
        if not re.fullmatch(r"[A-Za-z0-9-]+", owner) or not re.fullmatch(
            r"[A-Za-z0-9._-]+", repository
        ):
            raise GitHubAnalysisError(400, "The registered GitHub repository URL is invalid.")
        return owner, repository

    @classmethod
    async def _get_json(
        cls,
        client: httpx.AsyncClient,
        url: str,
        *,
        required: bool = False,
        include_next: bool = False,
    ) -> dict | list | tuple[dict | list | None, str | None] | None:
        try:
            response = await client.get(url)
        except httpx.TimeoutException as error:
            raise GitHubAnalysisError(
                504,
                "GitHub request timed out. Try again later.",
            ) from error
        except httpx.RequestError as error:
            raise GitHubAnalysisError(
                502,
                "Could not reach GitHub. Check network access and try again.",
            ) from error

        if response.status_code == 404 and required:
            raise GitHubAnalysisError(404, cls._not_found_message())
        if response.status_code in (403, 429):
            if cls._is_rate_limited(response):
                raise GitHubAnalysisError(
                    429,
                    "GitHub API rate limit reached. Wait before retrying.",
                )
            if not required:
                return (None, None) if include_next else None
            raise GitHubAnalysisError(
                403,
                "GitHub denied access to this repository. Check the backend token and its repository permissions.",
            )
        if response.status_code in (404, 409) and not required:
            return (None, None) if include_next else None
        if response.status_code == 401:
            raise GitHubAnalysisError(
                502,
                "GitHub rejected the backend GITHUB_TOKEN. Check the token or remove it to use public unauthenticated access.",
            )
        if response.is_error:
            raise GitHubAnalysisError(
                502,
                f"GitHub API returned HTTP {response.status_code}. Try again later.",
            )
        try:
            payload = response.json()
        except ValueError as error:
            raise GitHubAnalysisError(
                502,
                "GitHub returned an invalid JSON response.",
            ) from error
        if not isinstance(payload, (dict, list)):
            raise GitHubAnalysisError(502, "GitHub returned an unexpected response shape.")
        if include_next:
            return payload, cls._next_page_url(response.headers.get("Link"))
        return payload

    @staticmethod
    def _not_found_message() -> str:
        return (
            "GitHub repository not found or inaccessible. Check the URL and, for a "
            "private repository, configure a backend GITHUB_TOKEN with access."
        )

    @staticmethod
    def _is_rate_limited(response: httpx.Response) -> bool:
        return (
            response.status_code == 429
            or response.headers.get("x-ratelimit-remaining") == "0"
            or "rate limit" in response.text.lower()
        )

    @classmethod
    async def _get_paginated(
        cls,
        client: httpx.AsyncClient,
        url: str,
    ) -> tuple[list[dict], str]:
        records: list[dict] = []
        separator = "&" if "?" in url else "?"
        page_url: str | None = f"{url}{separator}per_page={GITHUB_PAGE_SIZE}&page=1"

        for _ in range(GITHUB_MAX_PAGES):
            if page_url is None:
                break
            if not cls._is_github_api_url(page_url):
                raise GitHubAnalysisError(502, "GitHub returned an unsafe pagination URL.")
            result = await cls._get_json(client, page_url, include_next=True)
            if not isinstance(result, tuple):
                raise GitHubAnalysisError(502, "GitHub pagination response was invalid.")
            payload, next_url = result
            if payload is None:
                return records, "inaccessible or unavailable from GitHub"
            if "actions/runs" in url:
                if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
                    raise GitHubAnalysisError(502, "GitHub returned an invalid workflow-runs response.")
                page_records = payload["workflow_runs"]
            else:
                if not isinstance(payload, list):
                    raise GitHubAnalysisError(502, "GitHub returned an invalid list response.")
                page_records = payload
            if not all(isinstance(item, dict) for item in page_records):
                raise GitHubAnalysisError(502, "GitHub returned malformed repository records.")
            records.extend(page_records)
            page_url = next_url
        else:
            return records, f"available (first {GITHUB_MAX_PAGES * GITHUB_PAGE_SIZE} records)"

        return records, "available" if records else "available; no records returned"

    @staticmethod
    def _is_github_api_url(url: str) -> bool:
        parsed = urlsplit(url)
        try:
            port = parsed.port
        except ValueError:
            return False
        return (
            parsed.scheme == "https"
            and parsed.hostname == "api.github.com"
            and parsed.username is None
            and parsed.password is None
            and port in (None, 443)
        )

    @staticmethod
    def _next_page_url(link_header: str | None) -> str | None:
        if not link_header:
            return None
        match = re.search(r'<([^>]+)>\s*;\s*rel="?next"?', link_header)
        return match.group(1) if match else None

    @staticmethod
    def _repository_metadata(payload: dict | list | None) -> RepositoryMetadata:
        if not isinstance(payload, dict):
            raise GitHubAnalysisError(502, "GitHub returned invalid repository metadata.")
        required = ("name", "full_name", "html_url", "visibility", "default_branch")
        if any(not isinstance(payload.get(key), str) for key in required):
            raise GitHubAnalysisError(502, "GitHub returned incomplete repository metadata.")
        return RepositoryMetadata(
            name=payload["name"],
            full_name=payload["full_name"],
            description=payload.get("description"),
            html_url=payload["html_url"],
            visibility=payload["visibility"],
            language=payload.get("language"),
            default_branch=payload["default_branch"],
            is_fork=payload.get("fork", False),
            is_archived=payload.get("archived", False),
            stargazers_count=payload.get("stargazers_count", 0),
            forks_count=payload.get("forks_count", 0),
            open_issues_count=payload.get("open_issues_count", 0),
            created_at=payload.get("created_at"),
            updated_at=payload.get("updated_at"),
            pushed_at=payload.get("pushed_at"),
        )

    @staticmethod
    def _issue_record(item: dict) -> dict:
        number = item.get("number")
        return {
            "id": f"issue-{number}",
            "title": item.get("title") or "",
            "description": item.get("body") or "",
            "html_url": item.get("html_url"),
            "ref": f"#{number}",
            "created_at": item.get("created_at"),
        }

    @staticmethod
    def _pull_request_record(item: dict) -> dict:
        number = item.get("number")
        return {
            "id": f"pull-{number}",
            "title": item.get("title") or "",
            "description": item.get("body") or "",
            "html_url": item.get("html_url"),
            "ref": f"#{number}",
            "created_at": item.get("created_at"),
        }

    @staticmethod
    def _commit_record(item: dict) -> dict:
        commit = item.get("commit") or {}
        author = commit.get("author") or {}
        committer = commit.get("committer") or {}
        message = commit.get("message") or ""
        return {
            "id": f"commit-{item.get('sha', 'unknown')}",
            "title": message.splitlines()[0] if message else "",
            "description": message,
            "html_url": item.get("html_url"),
            "sha": item.get("sha"),
            "created_at": author.get("date") or committer.get("date"),
        }

    @staticmethod
    def _workflow_record(item: dict) -> dict:
        run_id = item.get("id", "unknown")
        conclusion = item.get("conclusion")
        status = conclusion or item.get("status") or "unknown"
        return {
            "id": f"workflow-{run_id}",
            "title": item.get("name") or "",
            "description": (
                f"GitHub Actions run status: {item.get('status', 'unknown')}; "
                f"conclusion: {conclusion or 'not concluded'}."
            ),
            "html_url": item.get("html_url"),
            "ref": str(run_id),
            "created_at": item.get("created_at"),
            "status": status,
        }

    @staticmethod
    def _live_blocker(index: int, diagnosis, evidence_by_id: dict[str, Evidence]) -> BlockerResult:
        evidence_items = [
            evidence_by_id[item_id]
            for item_id in diagnosis.evidence_ids
            if item_id in evidence_by_id
        ]
        has_source_url = any(item.source_url for item in evidence_items)
        return BlockerResult(
            id=f"blocker-{index}",
            title=diagnosis.blocker,
            explanation=diagnosis.explanation,
            impact="A failed workflow may block changes if it is configured as a required check.",
            severity="high",
            confidence=diagnosis.confidence,
            evidence_ids=[
                item_id
                for item_id in diagnosis.evidence_ids
                if item_id in evidence_by_id
            ],
            recommended_actions=[
                "Open the GitHub Actions run and inspect its failing job and step."
                if has_source_url
                else "Inspect the failed GitHub Actions workflow and identify its first failing step; no run URL was provided."
            ],
        )

    @staticmethod
    def _live_summary(
        repository: str,
        metadata: dict | list | None,
        availability: dict[str, str],
        blockers: list[BlockerResult],
    ) -> str:
        if not isinstance(metadata, dict):
            raise GitHubAnalysisError(502, "GitHub returned invalid repository metadata.")
        blocker_summary = (
            f"{len(blockers)} failed workflow blocker(s) detected."
            if blockers
            else "No failed workflow blocker was detected in the retrieved evidence."
        )
        limited = [
            f"{key}: {value}"
            for key, value in availability.items()
            if value != "available" and not value.startswith("available;")
        ]
        limitation = f" Some data was unavailable ({'; '.join(limited)})." if limited else ""
        return (
            f"Live GitHub data retrieved for {repository} "
            f"(default branch: {metadata.get('default_branch', 'unknown')}). "
            f"{blocker_summary}{limitation}"
        )
