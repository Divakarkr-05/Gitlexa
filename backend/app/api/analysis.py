"""Analysis API routes skeleton."""
from fastapi import APIRouter
from app.schemas.analysis import AnalysisRequest, AnalysisResponse

router = APIRouter()

@router.post("/run", response_model=AnalysisResponse)
async def trigger_analysis(payload: AnalysisRequest):
    raise NotImplementedError("Analysis trigger to be implemented")
