# Gitlexa Frontend Implementation Specification

> **Status**: `FINALIZED`
>
> Scope is based on the visible portion of the user-provided specification. The pasted
> source ended during its code-quality section; no requirements from the missing portion
> are inferred.

## Vision

Deliver a polished, responsive developer workspace for Gitlexa that makes repository
health and blockers easy to scan and provides an immediately discoverable Alexa+ demo
assistant. The frontend must distinguish simulated content from live backend data and
must not imply integrations that do not exist.

## Goals

1. **Create a premium monitoring dashboard** — Show repository identity and health,
   issues and pull-request summaries, workflow status, activity, commits, and blockers.
2. **Make Alexa+ the main interaction** — Provide a full-screen, keyboard-accessible
   assistant with a deterministic, visibly simulated text conversation.
3. **Make the existing app navigable** — Add responsive top navigation across Dashboard,
   Project, Analysis, and Settings without adding a routing dependency.
4. **Use backend contracts truthfully** — Keep API access in service modules, use only
   existing `/api/v1` routes, and retain labeled demo content when live telemetry is
   unavailable.
5. **Preserve deployment compatibility** — Keep the static Vite build and current
   Docker/Nginx deployment approach working with configurable API base URL behavior.
6. **Provide an honest account-entry experience** — Add a polished login screen, an
   explicitly insecure demo-access session, and a sample profile without implying that
   user authentication or profile persistence exists.

## Non-Goals

- Real GitHub telemetry, repository polling, or direct browser-to-GitHub requests.
- Real email/password authentication, user accounts, or durable profile storage unless
  a verified backend capability is added in a future scope.
- Real Bedrock responses, Alexa hosted-service/account access, voice streaming, or a
  microphone implementation.
- Backend, Alexa, MCP, IAM, infrastructure, or deployment-architecture changes.
- Adding a routing, component, animation, or visual asset dependency.
- Committing, pushing, deploying, or changing Git history.

## Constraints

- Work within `frontend/`; do not modify the backend, Alexa module, or infrastructure.
- Use React 18, TypeScript, Vite, existing `lucide-react`, and CSS.
- Respect `.ai/API_CONTRACTS.md` and actual backend routes. Available routes are
  `GET /api/v1/health`, `POST /api/v1/projects`, `POST /api/v1/analysis/run`, and
  `GET /api/v1/auth/status`; no telemetry listing or analysis-result GET route exists.
- Default to a demo-first experience that does not need backend credentials. Label all
  simulated telemetry and assistant responses with `DEMO DATA — NOT LIVE GITHUB TELEMETRY`
  or an equally clear, visible simulated-response indicator.
- API failure must be visible and must not be represented as healthy/live data.
- Support desktop, tablet, and mobile; semantic HTML, keyboard navigation, visible focus,
  accessible labels, contrast, and reduced motion are required.
- The only current auth route is `GET /api/v1/auth/status`, which reports whether a GitHub
  token is configured; it is not a user sign-in endpoint. Do not send or persist login
  credentials. Demo access must be visibly labeled as a client-side, non-secure session.
- The profile menu must provide Profile, Settings, and Sign out. The profile page must
  clearly identify its display name/email as sample demo data and not claim persistence.
- No new dependencies or external assets. Avoid reliance on externally hosted fonts.
- Do not commit or otherwise modify Git history without explicit approval.
- Keep the current Docker build viable and document `VITE_API_BASE_URL` if introduced.

## Success Criteria

- [ ] Dashboard renders a useful first-visit experience with clearly labeled synthetic data.
- [ ] Dashboard shows repository health, issues/PRs, CI, recent activity/commits, blockers,
  and an Alexa+ entry point without presenting fabricated values as live.
- [ ] Dashboard, Project, Analysis, and Settings are reachable via responsive top navigation.
- [ ] Alexa+ opens a full-screen experience and supports close/return, suggested prompts,
  text submission, processing feedback, and visibly simulated responses.
- [ ] No fake microphone, GitHub connection, Bedrock connection, or live telemetry status
  is presented.
- [ ] Existing backend health, project creation, and analysis-run contracts are implemented
  in frontend service modules and handle HTTP/network failures explicitly.
- [ ] Responsive, keyboard, screen-reader, focus, and reduced-motion behaviors are present.
- [x] A responsive login screen offers a clearly labeled demo-access flow and does not
  claim real email/password authentication.
- [x] The workspace is gated by in-memory demo-session state; sign out clears it and returns
  to login. Profile and Settings remain reachable from an accessible avatar menu.
- [x] The profile page clearly labels sample identity details and does not imply saved
  account changes.
- [ ] `npm run build` succeeds, relevant tests or focused checks pass, and a screenshot of
  the working UI is captured.
- [ ] No commit, push, deploy, or Git history change is made.

## User Stories

### As a repository maintainer

- I want to see repository health and blockers at a glance.
- So that I can quickly understand what needs attention.

### As a first-time user

- I want a useful demo without credentials and clear labels for simulated content.
- So that I can explore the experience without mistaking sample values for telemetry.

### As an assistant user

- I want to ask a suggested or custom text question in an immersive Alexa+ interface.
- So that I can explore the interaction without a false claim of live AI or voice access.

## Technical Requirements

| Requirement | Priority | Notes |
|-------------|----------|-------|
| Responsive dashboard and top navigation | Must-have | No permanent left sidebar or new router |
| Full-screen simulated Alexa+ conversation | Must-have | Text-only; explicitly labeled simulation |
| Existing API service contracts | Must-have | Use only routes verified in the backend |
| Accessible interaction and reduced motion | Must-have | Semantic, keyboard, focus, and labels |
| Configurable API base URL | Must-have | Default and deployment behavior documented |
| Demo login and profile UX | Must-have | No real user-auth endpoint exists; credentials stay in the browser form only and are never sent or persisted |
| Additional external libraries/assets | Out of scope | Existing dependencies and CSS suffice |

## Targeted Screen-Fit Refinement

- Keep the current Gitlexa visual design and interactive behavior while fixing viewport sizing,
  responsive layouts, and Alexa+ readability.
- Use border-box sizing throughout; ensure `html`, `body`, and `#root` occupy the available
  width and have an appropriate `100vh` fallback plus `100dvh` minimum height.
- Prevent accidental horizontal overflow, preserve intentional page and conversation
  scrolling, and allow grid/flex children to shrink.
- Ensure the dashboard cards and content grids adapt to viewport width and stack cleanly
  on mobile.
- Use readable assistant typography (heading `clamp(2rem, 4vw, 3.25rem)`, message text
  around `1.125rem` desktop and readable mobile size, suggestions at least `1rem`, and
  a comfortable ~52–60px composer input).
- Keep the assistant orb prominent while ensuring heading, conversation, suggestions, and
  composer remain visible or reachable by intentional scrolling.
- Continue to respect reduced-motion preferences and clearly label all assistant output
  as simulated.

---

*Last updated: 2026-10-22*
