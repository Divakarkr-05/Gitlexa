"""Authentication endpoints."""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import AuthStatusResponse

router = APIRouter()


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    """Report GitHub token configuration, not credential validity or user identity."""
    token_value = settings.get_github_token_value()
    return AuthStatusResponse(
        configured=bool(token_value and token_value.strip()),
        provider="github",
    )