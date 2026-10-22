"""Project configuration routes."""

import re
from uuid import uuid4
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException

from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()

# Process-local project store for the demo. Duplicate registrations are allowed and create
# separate project IDs, matching the existing behavior.
projects: dict[str, ProjectResponse] = {}


def _validate_github_repo_url(repo_url: str) -> str:
    """Return a trimmed HTTPS GitHub repository URL or raise a clear client error."""
    normalized_url = repo_url.strip()
    error_detail = (
        "repo_url must be an HTTPS GitHub repository URL in the form "
        "https://github.com/{owner}/{repo}"
    )

    if not normalized_url or any(character.isspace() for character in normalized_url):
        raise HTTPException(status_code=400, detail=error_detail)

    try:
        parsed_url = urlsplit(normalized_url)
        port = parsed_url.port
    except ValueError:
        raise HTTPException(status_code=400, detail=error_detail) from None

    if (
        parsed_url.scheme.lower() != "https"
        or parsed_url.hostname is None
        or parsed_url.hostname.lower() != "github.com"
        or parsed_url.username is not None
        or parsed_url.password is not None
        or port not in (None, 443)
        or parsed_url.netloc.endswith(":")
        or parsed_url.query
        or parsed_url.fragment
        or "?" in normalized_url
        or "#" in normalized_url
        or "%" in parsed_url.path
        or "\\" in parsed_url.path
    ):
        raise HTTPException(status_code=400, detail=error_detail)

    path = parsed_url.path.removeprefix("/")
    path_parts = path.split("/")
    if len(path_parts) != 2:
        raise HTTPException(status_code=400, detail=error_detail)

    owner, repository = path_parts
    repository_name = repository.removesuffix(".git")
    if (
        not re.fullmatch(r"[A-Za-z0-9-]+", owner)
        or owner in {".", ".."}
        or not re.fullmatch(r"[A-Za-z0-9._-]+", repository_name)
        or repository_name in {"", ".", ".."}
    ):
        raise HTTPException(status_code=400, detail=error_detail)

    return normalized_url


@router.post("", response_model=ProjectResponse)
async def create_project(payload: ProjectCreate) -> ProjectResponse:
    """Register a structurally valid GitHub repository URL; does not verify access."""

    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Project name cannot be empty")

    repo_url = _validate_github_repo_url(payload.repo_url)

    project_id = str(uuid4())

    project = ProjectResponse(
        id=project_id,
        name=payload.name.strip(),
        repo_url=repo_url,
    )

    projects[project_id] = project

    return project