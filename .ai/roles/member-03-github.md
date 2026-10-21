# Member 03: GitHub Integration

## Ownership
- **Directories**:
  - `backend/app/github/`
- **Technologies**: GitHub REST/GraphQL API, HTTP clients (httpx), PyGithub, GitHub Webhooks, Telemetry Ingestion.

## Core Responsibilities
1. **GitHub Data Retrieval**:
   - Implement clients for fetching issues, pull requests, commits, CI/workflow runs, and code searches.
   - Handle GitHub authentication, pagination, rate-limit caching (`ETag`), and error recovery.
2. **Telemetry Ingestion**:
   - Provide clean, typed GitHub data primitives for Member 01's Evidence Engine.

## Strict Boundaries
- **MUST NOT** own or implement `backend/app/evidence/` (owned exclusively by Member 01).
- Member 03 retrieves raw repository data; Member 01 correlates and scores evidence into blockers.
- Do not build agent reasoning or MCP server layers (owned by Member 02).
