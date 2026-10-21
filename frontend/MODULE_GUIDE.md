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
  - The frontend currently has no live repository telemetry or analysis-result API.
    Any sample repository data or assistant responses must be labeled as simulated.
  - The login screen does not authenticate users: the only backend auth route is
    `GET /api/v1/auth/status`, which reports GitHub-token configuration. Demo access is
    a volatile client-side preview flag, not secure authorization. Login credentials
    are not sent or persisted; profile details are fixed sample data.
