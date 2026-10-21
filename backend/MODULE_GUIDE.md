# Module Guide: Backend Core

This guide outlines directory structure, active focus areas, and technical responsibility boundaries across the backend to prevent merge conflicts and avoid duplicated implementations.

> **Note**: [.ai/TEAM_ROLES.md](file:///c:/Users/Divakar%20K%20R/Gitlexa/.ai/TEAM_ROLES.md) remains the authoritative source for overall team responsibilities.

## Directory Responsibilities & Current Contributors

| Directory | Current Contributors | Responsibilities |
|---|---|---|
| `backend/app/core/` | **Member 01** | Configuration, logging, security, exception hierarchies |
| `backend/app/evidence/` | **Member 01** | Evidence schemas, correlation, blocker detection, scoring |
| `backend/app/agent/` | **Member 02** | Agent orchestrator, planner, decision engine, prompts |
| `backend/app/mcp/` | **Member 02** | MCP server, transport, MCP tools (`list_issues`, etc.) |
| `backend/app/github/` | **Member 03** | GitHub REST/GraphQL clients, data retrieval (No Evidence logic) |
| `backend/app/api/` | **Shared / Collaborative** | REST route definitions connecting services |
| `backend/app/models/` | **Shared / Collaborative** | Shared database entities |
| `backend/app/schemas/` | **Shared / Collaborative** | Pydantic contracts |
| `backend/tests/unit/` | **Member 06** | Unit tests |
| `backend/tests/integration/` | **Member 06** | Subsystem integration tests |
| `backend/tests/evaluation/` | **Member 01** | Evaluation benchmarks and scenarios |

## Collaboration Boundaries
To maintain architectural integrity and clear separation of concerns:
- **Evidence Engine Exclusivity**: The Evidence Engine in `backend/app/evidence/` is developed and maintained exclusively by Member 01.
- Member 03 focuses on GitHub client data retrieval and does not implement evidence correlation or scoring logic.
- Member 02 focuses on agent planning, reasoning, and MCP tooling and delegates evidence gathering to the Evidence Engine.
- Member 06 focuses on unit and integration test coverage and does not create an alternative evidence engine implementation.
