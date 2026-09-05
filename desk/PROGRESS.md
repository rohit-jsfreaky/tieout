# PROGRESS — desk/

> Working memory for this folder. Read first, update before ending every session.

## Current state — 2026-09-05

- **4a DONE.** Next.js skeleton + design system on screen. `npm run dev` renders the styled
  empty four-zone layout; `npm run typecheck`, `npm run lint` and `npm run build` are clean.
- 4b/4c/4d not started. Still correctly blocked on the API (Phase 3) for any real data.

## Done

- **4a — skeleton + design system.**
  - create-next-app (TS strict, Tailwind v4, App Router, no `src/`, ESLint). All boilerplate
    stripped: default page, favicon, `public/*.svg`, generated README/AGENTS. `next` came out
    at **16.3.4**, which is the published `latest` — no hand-fix needed this time.
  - `app/globals.css` is the whole design system, ported from Cairn's: `@theme` with three
    inks + two grounds + ONE accent, the 4px-stepped radius scale (`--radius-xs` 6px →
    `--radius-3xl` 40px), `corner-shape: squircle` globally with `.rounded-full` opting back
    out, and the four inset-shadow depth utilities (`surface`, `surface-raised`,
    `surface-floating`, `well`) plus `hairline`, copied verbatim.
  - Fonts are Tieout's own, not Cairn's: **Fraunces Variable** (display),
    **Geist Variable** (body), **Geist Mono Variable** (figures), self-hosted via
    `@fontsource-variable/*`.
  - `font-variant-numeric: tabular-nums` on `body`, so every figure on the screen aligns
    without anyone remembering to ask.
  - Layout: counters strip on top, QUEUE / EVIDENCE PACK / POLICIES side by side with
    hairline dividers, controls along the bottom. Styled, no data.
  - `lib/api-types.ts` + `lib/api.ts` — typed stubs for the seven Phase 3 routes plus the SSE
    URL. `api.ts` throws until 4b puts a fetch behind `request`; nothing fetches yet.

## Next action

4b from PLAN.md — queue + evidence pack, once the API's Phase 3 finish line passes.

## Decisions made

- One page. The "cleared by SHORT-SHIP-01 · Chris, Controller" row is the product moment.
- Fraunces + Geist + Geist Mono + inset shadows + squircles (Rohit's locked taste; Cairn's
  Shantell/Hanken pair stays Cairn's).
- **Accent: ledger blue `#14508c`** (`--color-ledger`). Cairn's moss is taken. Used for
  eyebrows, ticks and the winning number only — nowhere else.
- Numbers live in Geist Mono, headings in Fraunces at weight 450–500, never bold.
- Empty counters read **"—"**, never `0`. A figure on this screen only ever comes from a real
  run (root rule 6).
- No chart library — counters and a confidence bar drawn as a `well` track.
- **@phosphor-icons/react not installed yet.** 4a has nothing for an icon to do and the folder
  rule is "no unused deps". Add it in 4b, where source chips and status badges need it.
- API base comes from `NEXT_PUBLIC_API_BASE`, defaulting to `http://localhost:8700`.

## Notes for 4b

- `lib/api-types.ts` was written from `backend/PLAN.md` Phase 3, before `api/schemas.py`
  exists. **Reconcile the two the moment 3a lands.** One known guess: `class` is a Python
  keyword, so the exception's class is typed as `exception_class` here.
- Next 16 appended its own `nextjs-agent-rules` block to `desk/CLAUDE.md` on first `next dev`.
  It is regenerated on every dev run — commit it, do not delete it.
- The container rhythm is Cairn's `max-w-[1280px]` + `px-6` + `border-black/6` hairlines, but
  the vertical rhythm is NOT Cairn's `py-24/py-32`. This is a full-height desk, not a landing
  page: the header is `py-6`, the footer `py-4`, and the three zones scroll inside `h-dvh`.

## Blockers

- Phase 3 not done. 4b cannot start until `curl :8700/queue` works.

## Session log

- **2026-09-03** — folder created, plan written. No code.
- **2026-09-05** — 4a built: Next 16.3.4 skeleton, design system ported from Cairn with new
  fonts and a new accent, empty four-zone layout, typed API stubs. Verified with a real
  `next dev` (page 200, fonts and compiled utilities served), `tsc --noEmit`, `eslint`,
  `next build` — all clean.
