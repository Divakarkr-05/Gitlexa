"""Project configuration routes skeleton."""
from fastapi import APIRouter
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()

@router.post("", response_model=ProjectResponse)
async def create_project(payload: ProjectCreate):
    raise NotImplementedError("Project registration to be implemented")
