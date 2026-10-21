# Module Guide: Frontend Web Dashboard

This guide outlines the scope, responsibilities, and architectural boundaries for the web dashboard application.

> **Note**: [.ai/TEAM_ROLES.md](file:///c:/Users/Divakar%20K%20R/Gitlexa/.ai/TEAM_ROLES.md) remains the authoritative source for overall team responsibilities.

## Module Responsibilities
- **Current Contributors**: Member 04 (Frontend Specialist)
- **Scope**: React 18, Vite, TypeScript, Component library, Telemetry dashboards, Real-time status views.
- **Architectural Boundaries**:
  - Consumes `/api/v1` backend endpoints exclusively.
  - No direct AWS or GitHub token exposure in client-side code.
