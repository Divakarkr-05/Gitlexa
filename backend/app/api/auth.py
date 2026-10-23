from typing import Any, Dict
from fastapi import APIRouter

from app.core.config import settings
from app.github.app_auth import github_app_auth
from app.schemas.common import AuthStatusResponse

router = APIRouter()


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    """Report GitHub token or App configuration, not credential validity or user identity."""
    token_value = settings.get_github_token_value()
    is_app_configured = settings.is_github_app_configured()
    return AuthStatusResponse(
        configured=bool((token_value and token_value.strip()) or is_app_configured),
        provider="github",
    )


@router.get("/app/status")
async def github_app_status() -> Dict[str, Any]:
    """Report GitHub App installation status (without exposing secrets or tokens)."""
    return github_app_auth.get_public_status()