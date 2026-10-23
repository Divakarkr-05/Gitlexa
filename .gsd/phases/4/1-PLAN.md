---
phase: 4
plan: 1
wave: 1
depends_on: []
files_modified:
  - frontend/src/App.tsx
  - frontend/src/index.css
  - frontend/src/pages/Dashboard.tsx
  - frontend/src/pages/Login.tsx
  - frontend/src/pages/Profile.tsx
autonomous: true
user_setup: []

must_haves:
  truths:
    - "Users can enter the workspace only through an explicitly labeled client-side demo session."
    - "Email/password submission never claims success and sends or persists no credentials."
    - "The profile menu supports Profile, Settings, and Sign out with keyboard and outside-click dismissal."
    - "The profile page labels identity details as sample demo data and makes no persistence claim."
    - "Dashboard, existing navigation, and Alexa+ remain available during the demo session."
  artifacts:
    - "frontend/src/pages/Login.tsx renders the accessible login and demo-access screen."
    - "frontend/src/pages/Profile.tsx renders the sample profile page."
    - "frontend/src/App.tsx gates the workspace and wires menu/session navigation."
    - "frontend/src/index.css styles the new surfaces responsively."

# Plan 4.1: Demo login and profile experience

<objective>
Add a polished login view, clearly insecure demo-access flow, avatar menu, and sample profile
page to the existing Gitlexa frontend.

Purpose: Provide a complete account-entry and profile presentation without inventing real
authentication or disrupting existing workspace functionality.
Output: Login/demo-session flow, accessible profile dropdown, sample profile view, and responsive styling.
</objective>

<context>
Load for context:
- `.gsd/SPEC.md`
- `PROJECT_RULES.md`
- `frontend/src/App.tsx`
- `frontend/src/index.css`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Settings.tsx`
- `frontend/src/services/api.ts`
- `backend/app/api/auth.py`
</context>

<tasks>

<task type="auto">
  <name>Add honest login and demo-session gating</name>
  <files>frontend/src/App.tsx, frontend/src/pages/Login.tsx</files>
  <action>
    Build a responsive login screen with Gitlexa branding, labeled email/password inputs,
    password visibility toggle, visible focus, and accessible errors. Email/password submit
    must explain that user authentication is unavailable, that credentials were not sent or
    saved, and clear the password field. Provide a separate explicit demo-access action.
    Gate the existing workspace using volatile in-memory demo-session state; sign-out must
    clear that state and return to login. Treat GET /auth/status as configuration status,
    not authentication. Preserve Alexa+ and all existing page behavior.
    AVOID: sending, persisting, or echoing credentials, claiming real sign-in, or treating
    the demo flag as secure authorization.
  </action>
  <verify>Build frontend; browser-test invalid/unavailable credential submission, demo access, and sign-out.</verify>
  <done>Only explicit demo access opens the workspace; email/password never succeeds or leaves the page.</done>
</task>

<task type="auto">
  <name>Add accessible profile navigation and sample profile</name>
  <files>frontend/src/App.tsx, frontend/src/index.css, frontend/src/pages/Dashboard.tsx, frontend/src/pages/Profile.tsx</files>
  <action>
    Add a right-side initials/avatar disclosure menu with Profile, Settings, and Sign out.
    Support native keyboard activation, arrow-key menu navigation, Escape with focus return,
    and outside-click dismissal. Add a profile page showing fixed demo display name, email,
    avatar initials, and demo account type with explicit sample-data labeling; do not add
    profile editing or persistence. Extend the existing page type as needed and style both
    new screens/menu for desktop and mobile with the current charcoal/blue design.
    AVOID: adding routes/dependencies, implying real account details, or replacing Settings
    navigation or the Alexa+ control.
  </action>
  <verify>Browser-test menu activation/dismissal, Profile and Settings destinations, mobile layout, and Alexa+ launch.</verify>
  <done>Menu and profile are keyboard usable, clearly demo-labeled, responsive, and existing navigation still works.</done>
</task>

<task type="auto">
  <name>Verify all account and workspace flows</name>
  <files>frontend/src/App.tsx, frontend/src/index.css, frontend/src/pages/Dashboard.tsx, frontend/src/pages/Login.tsx, frontend/src/pages/Profile.tsx</files>
  <action>
    Run the frontend production build, inspect the Git diff/status, and exercise the login,
    demo, profile-menu, profile, sign-out, dashboard, and Alexa+ flows in desktop and mobile
    browser widths. Check horizontal overflow, focus behavior, and truthful authentication
    labeling. Update `.gsd/STATE.md` and this plan with verification evidence.
    AVOID: modifying backend authentication or committing/pushing; the user explicitly
    requested no Git history changes.
  </action>
  <verify>`npm run build` from `frontend`; browser interaction checks and screenshots; `git diff --check`; inspect `git status --short`.</verify>
  <done>Build and diff checks pass, required flows work, screenshots are captured, and no commit/push/deploy occurs.</done>
</task>

</tasks>

<verification>
- [x] Frontend build passes.
- [x] Credentials are not sent or persisted; demo access is explicitly non-secure.
- [x] Profile menu, Settings, Profile, sign-out, dashboard, and Alexa+ work.
- [x] Desktop and mobile screens have no accidental horizontal overflow at tested sizes.
- [x] Screenshots and final git status/diff are inspected; no commit or push is made.
</verification>

<success_criteria>
- [x] All tasks verified with browser/build evidence.
- [x] Authentication capabilities are reported accurately as real versus simulated.
</success_criteria>
