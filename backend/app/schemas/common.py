from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: Literal["gitlexa-backend"]


class AuthStatusResponse(BaseModel):
    configured: bool
    provider: Literal["github"]


class StatusMessage(BaseModel):
    status: str
    message: str
