from pydantic import BaseModel, ConfigDict

class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    repo_url: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    repo_url: str
