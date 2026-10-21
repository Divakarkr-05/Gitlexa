---
phase: 1
plan: 1
wave: 1
depends_on: []
files_modified:
  - frontend/src/App.tsx
  - frontend/src/components/AssistantExperience.tsx
  - frontend/src/index.css
  - frontend/src/pages/Dashboard.tsx
  - frontend/src/pages/Project.tsx
  - frontend/src/pages/Analysis.tsx
  - frontend/src/pages/Settings.tsx
  - frontend/src/services/api.ts
  - frontend/src/services/analysis.ts
  - frontend/src/services/projects.ts
  - frontend/src/types/index.ts
  - frontend/src/vite-env.d.ts
  - frontend/index.html
  - frontend/Dockerfile
  - frontend/nginx.conf
  - frontend/MODULE_GUIDE.md
autonomous: true
user_setup: []
must_haves:
  truths:
    - "Dashboard data is visibly identified as synthetic and not live GitHub telemetry."
    - "Top navigation switches among Dashboard, Project, Analysis, and Settings."
    - "Alexa+ opens a full-screen text assistant and returns deterministic, labeled demo responses."
    - "Only verified backend routes are used, through frontend service modules."
    - "The UI responds to narrow viewports and reduced-motion preferences."
  artifacts:
    - "frontend/src/App.tsx contains the app navigation and assistant state."
    - "frontend/src/pages/Dashboard.tsx presents monitoring sections and a clear Alexa+ entry point."
    - "frontend/src/services/api.ts implements explicit API errors and a configurable base URL."
    - "frontend/src/index.css defines the responsive and accessible visual system."

# Plan 1.1: Responsive repository workspace

<objective>
Build the frontend experience described in `.gsd/SPEC.md` using the repository's current
React, TypeScript, Vite, and Lucide dependencies.

Purpose: Give first-time users a polished, truthful demo while keeping all live API
communication inside service modules.
Output: Navigable dashboard pages, a full-screen text-only assistant demo, working
existing-contract services, and responsive accessible styling.
</objective>

<context>
Load for context:
- `.gsd/SPEC.md`
- `PROJECT_RULES.md`
- `frontend/MODULE_GUIDE.md`
- `frontend/src/App.tsx`
- `frontend/src/pages/`
- `frontend/src/services/`
- `backend/app/main.py`
- `backend/app/api/`
</context>

<tasks>

<task type="auto">
  <name>Implement truthful API services and domain types</name>
  <files>frontend/src/services/api.ts, frontend/src/services/analysis.ts, frontend/src/services/projects.ts, frontend/src/types/index.ts</files>
  <action>
    Implement a shared `/api/v1` request helper with a configurable `VITE_API_BASE_URL`,
    JSON handling, and explicit HTTP/network errors. Implement only the verified health,
    project-create, analysis-run, and auth-status contracts. Keep project and analysis
    request/response types accurate. Do not add unverified telemetry routes or treat
    service failures as successful demo/live data.
    AVOID: direct fetch calls from UI, broad catches, and invented API endpoints because
    the verified backend has no telemetry-list or analysis-result endpoint.
  </action>
  <verify>`cd frontend; npx tsc --noEmit`</verify>
  <done>All implemented service functions use typed `/api/v1` requests and surface failed requests as errors.</done>
</task>

<task type="auto">
  <name>Build responsive dashboard navigation and page states</name>
  <files>frontend/src/App.tsx, frontend/src/pages/Dashboard.tsx, frontend/src/pages/Project.tsx, frontend/src/pages/Analysis.tsx, frontend/src/pages/Settings.tsx</files>
  <action>
    Add accessible horizontal top navigation using the existing page components and a
    small local view-state solution; do not add a router. Create the monitoring dashboard
    with repository identity, health, issues/PRs, CI, recent activity/commits, blocker
    summary, empty/error/demo messaging, and a prominent Alexa+ action. Clearly label every
    simulated telemetry view as not live. Make project, analysis, and settings navigation
    render meaningful existing-scope content and keep any API errors explicit.
    AVOID: fabricated telemetry portrayed as live, dead navigation controls, and a
    permanent sidebar because they contradict the product requirements.
  </action>
  <verify>Run the frontend build and manually exercise every navigation destination.</verify>
  <done>All four navigation destinations render and dashboard demo values are visibly disclaimed.</done>
</task>

<task type="auto">
  <name>Implement the full-screen Alexa+ demo and accessible visual system</name>
  <files>frontend/src/App.tsx, frontend/src/components/AssistantExperience.tsx, frontend/src/index.css, frontend/index.html, frontend/vite.config.ts, frontend/Dockerfile, frontend/nginx.conf, frontend/MODULE_GUIDE.md</files>
  <action>
    Add a full-screen assistant view with animated CSS orb, assistant branding, status,
    labeled simulated conversation, keyboard-operable suggestions, text submission,
    processing feedback, return action, focus handling, and reduced-motion support. Style
    the workspace as a polished charcoal/electric-blue responsive interface. Use semantic
    elements, visible focus, contrast, accessible labels, and local/system fonts. Keep the
    existing Docker static-serving approach compatible and set the page metadata to match
    the finished app.
    AVOID: fake microphone controls, claims of actual Alexa/Bedrock integration, external
    assets, and animation that ignores reduced-motion preferences.
  </action>
  <verify>Build successfully, exercise assistant open/send/suggest/return interactions, and capture a screenshot of the running UI.</verify>
  <done>Assistant interactions are functional and visibly marked simulated; layout and motion adapt to viewport and accessibility preferences.</done>
</task>

</tasks>

<verification>
After all tasks, verify:
- [ ] `npm run build` succeeds.
- [ ] Dashboard and all navigation destinations render.
- [ ] Assistant opens, submits prompts, displays simulated replies, and closes.
- [ ] API errors are explicit; no unsupported telemetry API calls exist.
- [ ] UI works at desktop and mobile widths and honors reduced motion.
- [ ] Screenshot evidence is captured.
- [ ] No commit or other Git history change is made.
</verification>

<success_criteria>
- [ ] All task acceptance criteria pass.
- [ ] All must-haves are empirically confirmed.
</success_criteria>
