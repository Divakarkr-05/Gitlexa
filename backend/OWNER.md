# Subsystem Ownership: Backend Core

The backend is partitioned strictly among team members to prevent merge conflicts and overlapping implementations:

| Directory | Owner | Responsibilities |
|---|---|---|
| `backend/app/core/` | **Member 01** | Configuration, logging, security, exception hierarchies |
| `backend/app/evidence/` | **Member 01** | Evidence schemas, correlation, blocker detection, scoring |
| `backend/app/agent/` | **Member 02** | Agent orchestrator, planner, decision engine, prompts |
| `backend/app/mcp/` | **Member 02** | MCP server, transport, MCP tools (`list_issues`, etc.) |
| `backend/app/github/` | **Member 03** | GitHub REST/GraphQL clients, data retrieval (No Evidence logic) |
| `backend/app/api/` | **Shared / Lead** | REST route definitions connecting services |
| `backend/app/models/` | **Shared / Lead** | Shared database entities |
| `backend/app/schemas/` | **Shared / Lead** | Pydantic contracts |
| `backend/tests/unit/` | **Member 06** | Unit tests |
| `backend/tests/integration/` | **Member 06** | Subsystem integration tests |
| `backend/tests/evaluation/` | **Member 01** | Evaluation benchmarks and scenarios |

## Strict Rules
- Member 03 MUST NOT own or implement `backend/app/evidence/`.
- Member 02 MUST NOT implement the Evidence Engine.
- Member 06 MUST NOT create a second Evidence Engine.
