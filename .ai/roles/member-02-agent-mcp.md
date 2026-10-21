# Member 02: Agent + AI + Orchestration

## Ownership
- **Directories**:
  - `backend/app/agent/`
  - `backend/app/mcp/`
- **Technologies**: Model Context Protocol (MCP Python SDK), Amazon Bedrock Claude 3, Prompt Engineering, ReAct / Task Planning.

## Core Responsibilities
1. **Agent Orchestration**:
   - Build agent orchestrator, task planner, prompt management, and decision engine in `backend/app/agent/`.
   - Implement Bedrock LLM reasoning loops consuming evidence produced by Member 01.
2. **MCP Architecture**:
   - Implement the MCP Server and transport protocols in `backend/app/mcp/`.
   - Define MCP tools (`list_issues`, `get_pull_request`, `read_ci_status`, `search_code`, `draft_issue`) wrapping underlying services.

## Strict Boundaries
- **MUST NOT** implement the Evidence Engine (owned exclusively by Member 01).
- Rely on Member 01's Evidence Engine schemas and outputs.
- Rely on Member 03's GitHub client for raw GitHub API interactions.
