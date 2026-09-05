# PLAN — desk/ (Phase 4, 6 hours)

Finish line in `../MASTER-PLAN.md`. Needs the API's Phase 3 finish line.

### 4a. Skeleton + design system (75 min)
- create-next-app (TS, Tailwind, App Router), strip boilerplate, fix the `next` version.
- Fonts, Phosphor, tokens, one accent, inset-shadow card primitive, squircle corners.
- `lib/api.ts` + `lib/api-types.ts`.
- ✅ empty four-zone layout, styled, typecheck clean.

### 4b. Queue + evidence pack (120 min)
- Queue from `/queue`; click → pack from `/exceptions/{id}`; "Work" → `POST /work` and
  subscribe to `/events`; facts append live with source chip, time, screenshot thumbnail
  (portal facts). Proposed decision + confidence bar. Refusal state with "where I looked".
- ✅ E1 works end to end on screen with the portal screenshot visible.

### 4c. Decide + policies + counters (90 min)
- Approve/Reject/Edit with the approver name field → `POST /decide`; policy card appears on
  the right with the stamp. Counters from `/metrics`.
- Work E2 → row turns to "cleared by SHORT-SHIP-01 · Chris, Controller"; counter of human
  touches stays at 1.
- ✅ the four beats driven from the screen, no terminal.

### 4d. Polish (75 min)
- Loading/empty/error states; the reset button; a small transition when a rule is born.
- The 60-second stranger test (Phase 4 finish line).

### Deliberately NOT building
More pages, auth, settings, mobile, mock-data mode, charts.
