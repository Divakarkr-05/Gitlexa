from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    repo_url: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    repo_url: str
