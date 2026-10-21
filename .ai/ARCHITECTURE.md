# Gitlexa System Architecture

## Architecture Diagram

```
                             +-------------------------------+
                             |    Alexa Voice Interface      |
                             +---------------+---------------+
                                             |
                                             v (Speech / Intent)
+------------------------+       +-----------+--------------------+
| React Web Dashboard    | ----> |   Alexa MCP Client Bridge      |
| (Vite + TypeScript)    |       +-----------+--------------------+
+-----------+------------+                   |
            |                                |
            | HTTP / REST                    | JSON-RPC / MCP
            v                                v
+-----------------------------------------------------------------+
|                       FastAPI Backend Core                      |
|                                                                 |
|   +---------------------+             +---------------------+   |
|   |  Agent Orchestrator | <---------> | MCP Server & Tools  |   |
|   |  & Planner (Bedrock)|             | (stdio / SSE)       |   |
|   +----------+----------+             +----------+----------+   |
|              |                                   |              |
|              v                                   v              |
|   +---------------------+             +---------------------+   |
|   |   Evidence Engine   |             |   GitHub Client     |   |
|   |  (Blocker Detection)|             |   (API Wrappers)    |   |
|   +---------------------+             +---------------------+   |
+-----------------------------------------------------------------+
            |                                      |
            v                                      v
+------------------------+             +------------------------+
|     Amazon Bedrock     |             |       GitHub API       |
| (Claude 3 / Foundation)|             | (REST, GraphQL, CI)    |
+------------------------+             +------------------------+
```

## Subsystem Breakdown
1. **Frontend**: Vite + React 18 single-page application providing telemetry dashboards, blocker feeds, and project configuration.
2. **Backend**: FastAPI web server hosting REST endpoints, evidence correlation, and MCP tool registries.
3. **Agent & MCP**: Agent orchestrator coordinating Amazon Bedrock LLMs and registered MCP tools for multi-step reasoning.
4. **Alexa Skill**: Custom skill interaction model routing spoken voice queries to the MCP server.
5. **Infrastructure**: AWS IAM policies, Secrets Manager, CloudWatch telemetry, Docker Compose definitions.
