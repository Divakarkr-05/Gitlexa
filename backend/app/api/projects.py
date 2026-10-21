"""Project configuration routes."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()

# Temporary in-memory project store.
# Replace with the database repository once the persistence layer is wired.
projects: dict[str, ProjectResponse] = {}


@router.post("", response_model=ProjectResponse)
async def create_project(payload: ProjectCreate) -> ProjectResponse:
    """Register a GitHub project for analysis."""

    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Project name cannot be empty")

    if not payload.repo_url.startswith(
        ("https://github.com/", "http://github.com/")
    ):
        raise HTTPException(
            status_code=400,
            detail="repo_url must be a GitHub repository URL",
        )

    project_id = str(uuid4())

    project = ProjectResponse(
        id=project_id,
        name=payload.name.strip(),
        repo_url=payload.repo_url.strip(),
    )

    projects[project_id] = project

    return project