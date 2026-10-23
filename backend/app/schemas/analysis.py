from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.evidence.schemas import EvidenceType


AnalysisMode = Literal["demo", "live"]
AnalysisStatus = Literal["completed"]
BlockerSeverity = Literal["critical", "high", "medium", "low"]


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID
    mode: AnalysisMode = "demo"


class EvidenceResult(BaseModel):
    id: str
    type: EvidenceType
    title: str
    description: str
    source_url: str | None
    source_ref: str | None
    timestamp: datetime | None
    score: float = Field(ge=0.0, le=1.0)
    simulated: bool


class BlockerResult(BaseModel):
    id: str
    title: str
    explanation: str
    impact: str
    severity: BlockerSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str]
    recommended_actions: list[str]


class CorrelationResult(BaseModel):
    id: str
    evidence_ids: list[str]
    relationship: str
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)


class RepositoryMetadata(BaseModel):
    name: str
    full_name: str
    description: str | None
    html_url: str
    visibility: str
    language: str | None
    default_branch: str
    is_fork: bool
    is_archived: bool
    stargazers_count: int = Field(ge=0)
    forks_count: int = Field(ge=0)
    open_issues_count: int = Field(ge=0)
    created_at: datetime | None
    updated_at: datetime | None
    pushed_at: datetime | None


class AnalysisResponse(BaseModel):
    analysis_id: UUID
    project_id: UUID
    repository: str
    status: AnalysisStatus
    source: AnalysisMode
    simulated: bool
    analyzed_at: datetime
    repository_metadata: RepositoryMetadata | None
    data_availability: dict[str, str]
    summary: str
    blockers: list[BlockerResult]
    evidence: list[EvidenceResult]
    correlations: list[CorrelationResult]
