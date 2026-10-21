"""Authentication endpoints skeleton."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def auth_status():
    raise NotImplementedError("Auth status to be implemented")
