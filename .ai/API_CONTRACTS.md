# API & MCP Contracts

## 1. REST Endpoints (`/api/v1`)

### `GET /api/v1/health`
- **Description**: Service liveness and dependency status.
- **Response**: `{"status": "healthy", "service": "gitlexa-backend", "version": "0.1.0"}`

### `POST /api/v1/projects`
- **Description**: Register a new GitHub repository for monitoring.
- **Request**: `{"name": "Gitlexa", "repo_url": "https://github.com/owner/repo"}`
- **Response**: `{"id": "proj-xyz", "name": "Gitlexa", "repo_url": "https://github.com/owner/repo"}`

### `POST /api/v1/analysis/run`
- **Description**: Trigger repository health analysis and blocker detection.
- **Request**: `{"project_id": "proj-xyz"}`
- **Response**: `{"analysis_id": "an-123", "status": "queued", "project_id": "proj-xyz"}`

### `GET /api/v1/analysis/{analysis_id}`
- **Description**: Fetch detailed findings, blockers, and correlated evidence.
- **Response**: Detailed `AnalysisResponse` object.

---

## 2. Model Context Protocol (MCP) Tools

| Tool Name | Parameters | Returns | Description |
|---|---|---|---|
| `list_issues` | `repo: str`, `state: str` | `list[Issue]` | Retrieves open/closed issues with label filters |
| `get_pull_request` | `repo: str`, `pr_number: int` | `PullRequestDetails` | Retrieves PR status, review states, and diff summary |
| `read_ci_status` | `repo: str`, `branch: str` | `CIStatusSummary` | Returns latest GitHub Actions workflow run statuses |
| `search_code` | `repo: str`, `query: str` | `list[CodeMatch]` | Searches repository source code for patterns |
| `draft_issue` | `repo: str`, `title: str`, `body: str` | `DraftIssueResult` | Drafts a new issue based on blocker findings |
