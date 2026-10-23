---
phase: 3
plan: 1
wave: 1
depends_on: []
files_modified:
  - frontend/src/index.css
autonomous: true
user_setup: []
must_haves:
  truths:
    - "The root layout uses available viewport width and a 100vh/100dvh minimum height without accidental horizontal overflow."
    - "Dashboard cards and grids shrink responsively and stack on mobile."
    - "Alexa+ heading, conversation responses, prompts, and composer use readable sizes and comfortable touch targets."
    - "Assistant conversation scrolls independently as needed; the orb remains prominent and reduced motion remains respected."
  artifacts:
    - "frontend/src/index.css contains the responsive viewport and typography corrections."

# Plan 3.1: Responsive screen-fit refinement

<objective>
Make focused screen-fit and readability improvements to the existing frontend.

Purpose: Correct the current assistant panel's short intrinsic height and tiny text while
preventing viewport overflow at desktop and mobile sizes.
Output: Responsive root/dashboard sizing and readable Alexa+ layout with existing behavior
preserved.
</objective>

<context>
Load for context:
- `.gsd/SPEC.md`
- `frontend/src/App.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/components/AssistantExperience.tsx`
- `frontend/src/index.css`
</context>

<tasks>

<task type="auto">
  <name>Correct viewport and responsive dashboard constraints</name>
  <files>frontend/src/index.css</files>
  <action>
    Add root-level width and viewport-height fallbacks, allow the app/content grid children
    to shrink, make dashboard summary cards reflow with minmax(0, 1fr), and tighten mobile
    overflow behavior. Preserve normal document scrolling and the existing visual theme.
    AVOID: global overflow suppression, fixed content widths/heights, and 100vw sizing.
  </action>
  <verify>Browser-check dashboard at desktop and mobile widths; measure document width against the viewport.</verify>
  <done>Dashboard has no unintended horizontal overflow and cards remain usable across tested widths.</done>
</task>

<task type="auto">
  <name>Make full-screen Alexa+ content readable and viewport-aware</name>
  <files>frontend/src/index.css</files>
  <action>
    Make the assistant stage fit available viewport height while allowing page scrolling,
    stretch the conversation into its grid area, and let conversation messages scroll
    independently. Increase heading, response, prompt, input, labels, and touch targets
    to readable sizes; reduce only decorative spacing/orb size on mobile. Keep all
    functionality and reduced-motion rules.
    AVOID: hiding overflow to conceal clipped UI, shrinking text on mobile to fit, or
    removing simulated/demo labels.
  </action>
  <verify>Inspect screenshots and computed font/height/overflow values at 1440x960, 390x844, 320x720, and a short desktop viewport.</verify>
  <done>Heading, messages, suggestions, and composer are visible or reachable by intentional scroll without horizontal clipping.</done>
</task>

</tasks>

<verification>
- [x] `cd frontend; npm run build` succeeds.
- [x] Dashboard and assistant screenshots are checked at desktop and mobile sizes.
- [x] No horizontal overflow at 1440px, 390px, or 320px widths.
- [x] Assistant heading, replies, suggestions, composer height, and prompt text meet the specified readability targets.
- [x] Reduced-motion preference remains honored.
- [x] No commit or push is made.
</verification>

<success_criteria>
- [x] Both tasks are empirically verified.
- [x] Existing navigation and assistant behavior remain available.
</success_criteria>
