# Evidence schemas and data structures
"""Evidence data structures used by the Gitlexa evidence engine."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    CI_RUN = "ci_run"
    COMMIT = "commit"
    CODE = "code"
    LOG = "log"


class Evidence(BaseModel):
    """A single observable piece of evidence from a repository."""

    id: str
    type: EvidenceType
    title: str
    description: str

    source_url: str | None = None
    source_ref: str | None = None

    repository: str | None = None
    author: str | None = None

    timestamp: datetime | None = None

    # Evidence quality
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reliability_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Structured information returned by GitHub/CI tools.
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    """Collection of evidence gathered for one investigation."""

    repository: str
    collected_at: datetime = Field(default_factory=datetime.utcnow)

    evidence: list[Evidence] = Field(default_factory=list)

    def add(self, item: Evidence) -> None:
        """Add evidence to the bundle."""
        self.evidence.append(item)


class EvidenceScore(BaseModel):
    """Calculated strength of an evidence item."""

    evidence_id: str

    relevance: float = Field(ge=0.0, le=1.0)
    reliability: float = Field(ge=0.0, le=1.0)
    recency: float = Field(default=0.0, ge=0.0, le=1.0)

    overall_score: float = Field(ge=0.0, le=1.0)


class Correlation(BaseModel):
    """Relationship discovered between multiple evidence items."""

    id: str

    evidence_ids: list[str] = Field(default_factory=list)

    relationship: str
    explanation: str

    confidence: float = Field(ge=0.0, le=1.0)


class BlockerDiagnosis(BaseModel):
    """Evidence-backed diagnosis of a project blocker."""

    blocker: str
    explanation: str

    evidence_ids: list[str] = Field(default_factory=list)
    correlations: list[str] = Field(default_factory=list)

    confidence: float = Field(ge=0.0, le=1.0)

    recommended_actions: list[str] = Field(default_factory=list)