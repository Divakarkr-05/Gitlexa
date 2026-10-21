"""Analysis API routes."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.api.projects import projects
from app.schemas.analysis import AnalysisRequest, AnalysisResponse

router = APIRouter()


@router.post("/run", response_model=AnalysisResponse)
async def trigger_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    """Start an analysis for a registered project."""

    project = projects.get(payload.project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found: {payload.project_id}",
        )

    analysis_id = str(uuid4())

    return AnalysisResponse(
        analysis_id=analysis_id,
        status="queued",
        project_id=payload.project_id,
    )