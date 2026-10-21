# Gitlexa — Team Ownership Matrix

## Subsystem & Directory Ownership

| Member | Title | Owns Directories | Core Focus |
|---|---|---|---|
| **Member 01** | Cloud + AWS + Security + DevOps + Evidence Engine + Evaluation | `infra/`<br>`.github/`<br>`backend/app/core/`<br>`backend/app/evidence/`<br>`backend/tests/evaluation/` | Cloud infrastructure, CI/CD workflows, core config/security, evidence correlation engine, and evaluation benchmarks. |
| **Member 02** | Agent + AI + Orchestration | `backend/app/agent/`<br>`backend/app/mcp/` | Bedrock agent orchestrator, planner, decision engine, prompts, and MCP server/tools. |
| **Member 03** | GitHub Integration | `backend/app/github/` | GitHub REST/GraphQL API clients, issue/PR/commit/workflow data retrieval. *(Must NOT own evidence engine)*. |
| **Member 04** | Frontend | `frontend/` | React 18, Vite, TypeScript, telemetry dashboards, blocker views, UI components. |
| **Member 05** | Alexa+ Integration | `alexa/` | Alexa Skill interaction model, voice intents, and voice-to-MCP client bridge. |
| **Member 06** | QA + Integration Testing + Documentation | `backend/tests/unit/`<br>`backend/tests/integration/`<br>`docs/` | Unit testing, full integration testing suites, system and API documentation. *(Evaluation remains with Member 01)*. |

## Strict Ownership Boundaries
1. **Evidence Engine Exclusivity**:
   - `backend/app/evidence/` is owned **strictly and exclusively** by **Member 01**.
   - Member 03 MUST NOT own or implement `backend/app/evidence/`.
   - Member 02 MUST NOT implement the Evidence Engine.
   - Member 06 MUST NOT create a second Evidence Engine.
2. **Evaluation Ownership**:
   - `backend/tests/evaluation/` is owned by **Member 01** to validate the Evidence Engine and benchmarks.
   - Member 06 owns unit and integration testing (`backend/tests/unit/`, `backend/tests/integration/`).
3. **Data Dependency Flow**:
   ```
   GitHub Retrieval (Member 03)
            ↓
   Evidence Engine (Member 01)
            ↓
   Agent Reasoning & Orchestration (Member 02)
            ↓
   API Routing
            ↓
   Frontend (Member 04)  /  Alexa+ (Member 05)
   ```
