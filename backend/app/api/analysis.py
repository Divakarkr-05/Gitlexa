"""Analysis API routes."""

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException

from app.api.projects import projects
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import AnalysisService, GitHubAnalysisError

router = APIRouter()
analysis_results: dict[str, AnalysisResponse] = {}
analysis_service = AnalysisService()


@router.post("/run", response_model=AnalysisResponse)
async def trigger_analysis(payload: AnalysisRequest) -> AnalysisResponse:
    """Run and retain a completed demo analysis for a registered project."""

    project_id = str(payload.project_id)
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found: {project_id}",
        )

    try:
        if payload.mode == "live":
            result = await analysis_service.run_live(project, uuid4())
        else:
            result = analysis_service.run_demo(project, uuid4())
    except GitHubAnalysisError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    evidence_ids = {item.id for item in result.evidence}
    if any(
        not set(blocker.evidence_ids).issubset(evidence_ids)
        for blocker in result.blockers
    ):
        raise HTTPException(
            status_code=500,
            detail="Analysis result failed evidence integrity validation.",
        )

    analysis_results[str(result.analysis_id)] = result
    return result


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: UUID) -> AnalysisResponse:
    """Retrieve a completed analysis retained in this process."""

    result = analysis_results.get(str(analysis_id))
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis not found: {analysis_id}",
        )
    return result
