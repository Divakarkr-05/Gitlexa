# Gitlexa

> Voice & AI-Powered Repository Telemetry, Blocker Analysis, and MCP Intelligence.

Gitlexa combines GitHub API telemetry, Amazon Bedrock AI agent orchestration, Model Context Protocol (MCP) tool standards, and Alexa Voice interaction to help developers triage blockers, track CI health, and monitor pull requests effortlessly.

## Architecture

- **`backend/`**: FastAPI service orchestrating Bedrock, MCP tools, and GitHub telemetry.
- **`frontend/`**: React + TypeScript + Vite web dashboard.
- **`alexa/`**: Alexa skill models and voice-to-MCP bridges.
- **`infra/`**: Docker & AWS configurations (IAM, Bedrock, Secrets).
- **`.ai/`**: Shared architectural rules, API contracts, and team member role ownership.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Quick Setup
```powershell
./scripts/setup.ps1
./scripts/dev.ps1
```
