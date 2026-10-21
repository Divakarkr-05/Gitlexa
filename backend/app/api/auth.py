"""Authentication endpoints."""

from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/status")
async def auth_status():
    """Return whether the GitHub token is configured."""
    return {
        "authenticated": settings.get_github_token_value() is not None,
        "provider": "github",
    }