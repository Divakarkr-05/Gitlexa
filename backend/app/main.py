from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import health, analysis, projects, auth, github

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Gitlexa Backend API with MCP & Bedrock Agent integration",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub"])
