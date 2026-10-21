from pydantic import BaseModel
from typing import Optional

class AnalysisRequest(BaseModel):
    project_id: str

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    project_id: str
