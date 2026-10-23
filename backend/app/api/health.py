from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Report API process liveness without asserting dependency connectivity."""
    return HealthResponse(status="healthy", service="gitlexa-backend")
