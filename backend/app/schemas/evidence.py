from pydantic import BaseModel

class EvidenceItem(BaseModel):
    id: str
    source: str
    description: str
    severity: str
