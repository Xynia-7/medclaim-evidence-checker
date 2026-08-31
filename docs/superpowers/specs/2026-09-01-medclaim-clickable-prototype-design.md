# MedClaim clickable prototype design

Date: 2026-09-01

## Goal

Create one interview-ready, clickable demonstration of the existing MedClaim PRD. It must show how a medical content reviewer moves from a queued claim to evidence review and an auditable human decision. It is a portfolio prototype, not a clinical product.

## Options considered

1. **Static HTML, selected.** One dependency-free file is immediately runnable, versionable, inspectable, and easy to recreate in Figma as a personal exercise.
2. **Figma-only prototype.** Better for roles naming Figma, but an automatically generated file would not prove the user's own tool fluency and cannot be verified in the current workspace.
3. **Streamlit or full web application.** Adds runtime dependencies and backend behavior that the current interview story does not need.

## Scope

The prototype uses one public development example, MC003. No holdout gold, real patient data, diagnosis, prescription, or personalized advice may appear.

The single page has three views:

1. **Review queue:** one case, source, risk cue, and an `Open review` action.
2. **Evidence review:** claim, minimum evidence, population/line, source boundary, four label choices, and a human-review control.
3. **Decision record:** final human label, review route, case/source audit fields, and a `Review again` action.

## Interaction and state

- `Open review` changes the visible view without navigation or network calls.
- A decision cannot be submitted until one of the four allowed labels is selected.
- Missing selection produces an accessible inline error and moves focus to it.
- `Submit human decision` records the selected label and review route in the decision view.
- `Review again` resets the choice and returns to evidence review.
- Source links open the official public source in a new tab.

## Visual system

Use the same restrained white, black, gray, and blue system as the interview deck. Avoid dashboard cards beyond the one case row and one decision summary. Desktop uses a two-column evidence layout; narrow screens stack it. All controls need visible focus, text labels, and a non-color status cue.

## Boundaries

The interface must state that it is an offline portfolio prototype and that all outputs require human approval. It must not claim model confidence, clinical validity, time savings, production EHR integration, or automated release.

## Acceptance checks

1. The queue displays MC003 and opens the evidence view.
2. The evidence view shows the exact public claim, evidence summary, population/line, source, and four allowed labels.
3. Submitting without a label shows an error.
4. Selecting `Partial support`, keeping human review enabled, and submitting shows the same label and `Priority human review` in the decision record.
5. `Review again` clears the selection and returns to the evidence view.
6. The layout is usable at 1280×800 and 390×844.
7. Browser console contains no errors and the page makes no application data requests.

## Minimal implementation plan

1. Add one `medclaim-prototype.html` containing semantic HTML, CSS, sample data, and the state transitions.
2. Link it from the README and describe it as a clickable portfolio prototype.
3. Run a browser UAT covering the seven checks above and retain screenshots outside the repository.

## Deliberate omissions

No API, authentication, database, file upload, model call, reusable component library, or analytics. Add those only when a real role or user test requires them.
