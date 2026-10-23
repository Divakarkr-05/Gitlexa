# Module Guide: Frontend Web Dashboard

This guide outlines the scope, responsibilities, and architectural boundaries for the web dashboard application.

> **Note**: [.ai/TEAM_ROLES.md](file:///c:/Users/Divakar%20K%20R/Gitlexa/.ai/TEAM_ROLES.md) remains the authoritative source for overall team responsibilities.

## Module Responsibilities
- **Current Contributors**: Member 04 (Frontend Specialist)
- **Scope**: React 18, Vite, TypeScript, Component library, Telemetry dashboards, Real-time status views.
- **Architectural Boundaries**:
  - Consumes `/api/v1` backend endpoints exclusively.
  - No direct AWS or GitHub token exposure in client-side code.
  - `VITE_API_BASE_URL` optionally configures the API root and defaults to `/api/v1`.
    For Docker builds, provide it as a build argument; the default Nginx configuration
    proxies `/api/v1/` to the Compose `backend:8000` service.
  - Vite development serves `/api` through its local proxy to `http://localhost:8000`.
  - Live repository analysis is requested through the backend analysis API; the browser
    never calls authenticated GitHub endpoints directly.
  - The backend does not implement Gitlexa user registration, login, or sessions. Its
    only auth route is `GET /api/v1/auth/status`, which reports backend GitHub-token
    configuration and does not authenticate a user or validate the token.
  - The frontend must not simulate successful account access or display fabricated
    repository findings as live results. Live-analysis failures remain explicit.
