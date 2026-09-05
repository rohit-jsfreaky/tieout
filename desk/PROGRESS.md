# PROGRESS — desk/

> Working memory for this folder. Read first, update before ending every session.

## Current state — 2026-09-06 (after S5's hardening pass)

- **The four beats were driven through this screen five consecutive times** against a live
  `python -m tieout.api` and a real Chromium, from a Reset each round. Identical counters every
  round — **5 exceptions · 2 still open · 1 human touch · 1 auto-cleared · 1 refused ·
  16 evidence items · 3 screenshots** — and **no page errors of any kind**. Those are now the
  same numbers `tieout demo` prints; the earlier note about the evidence count moving between
  runs was measured before the fixes below and does not hold any more.
- **Two staleness bugs the repeated runs exposed, both in `lib/useDesk.ts`, both fixed:**
  1. **The whole counter strip could read `0` after Reset.** `loadBoard` asked for `/queue`,
     `/policies` and `/metrics` in one `Promise.all`. But `/queue` is the call that runs the
     three-way match and fills the engine's store, and `/metrics` only counts what is in it —
     so straight after a reset the counters could answer from an empty store. The queue is now
     awaited first and the counters read after it. (This screen also promised "empty reads —,
     never 0"; that promise was being broken by the ordering, not by the components.)
  2. **The counters lagged a whole beat behind the screen.** A run cleared `pending` the moment
     the stream said `done`, then refetched — so the refusal was readable on screen next to
     "Refused 0" for as long as the refetch took. `pending` now clears in a `.finally()` after
     the board and the pack have both come back, which also keeps the buttons disabled until
     what they act on is current.
  - Reads of the board are also numbered now, so the one fired when a run *starts* cannot land
    after the one fired when it *ends* and put the previous beat's counters back.
- **A seventh counter: "Still open"** — the exceptions nobody has picked up yet
  (`Metrics.open_not_worked`). Asked for by Rohit: the strip showed 5 found without ever
  saying that 2 of them had not been touched. Seven fit the strip comfortably at 1600px.
- `npm run typecheck`, `npm run lint` and `npm run build` clean.

## Earlier — 2026-09-06

- **4a, 4b, 4c and 4d are DONE.** The four beats can be driven from the screen with no
  terminal open, against a live `python -m tieout.api` on :8700. `npm run typecheck`,
  `npm run lint` and `npm run build` are clean.
- **No mock mode anywhere.** Every figure on the screen came out of `GET /metrics` or off the
  SSE stream in that session. `lib/api.ts` is still the only file that fetches.
- Verified by driving the real screen end to end (a throwaway Playwright script, since deleted)
  against a real run: the four beats passed and the header read
  **5 exceptions · 1 human touch · 1 auto-cleared · 1 refused · 12 evidence items ·
  3 screenshots**.

## Done

### 4b — queue + evidence pack

- `lib/api-types.ts` **rewritten against the real backend.** The 4a version was a guess from
  `backend/PLAN.md`; every shape is now mirrored from `engine/models.py` and `engine/events.py`
  in the same order, because `api/schemas.py` re-exports them unchanged. Pydantic
  `computed_field`s (`exposure`, `short_pct`, `Policy.ref`, …) are on the wire, so the desk
  never recomputes a number the engine published. The 4a guesses are gone: there is no
  `exception_class` (it is `kind`), no `Refusal` object (a refusal is a `Decision` with
  `action: "refuse"`), and the queue is `{count, exceptions: QueueRow[]}`, not a bare array.
- `lib/api.ts` — nine routes and one stream. `ApiError` carries FastAPI's own `detail`, so a
  409 reads "an investigation is already running on E1" rather than "Failed to fetch".
  `streamException` subscribes to all twelve `EventKind`s plus `done`, because sse-starlette
  names each message by the event's own `kind` — **there is no `message` listener to hang
  anything on**, which is the one thing that will silently break if someone adds a kind.
- `lib/useDesk.ts` — the whole state. Live events are merged into the fetched pack by id
  (facts) and by `source|action|locator|at` (steps), so the same list works mid-run and at
  rest with no second code path.
- Queue rows: class, status, billed amount, exposure, fact count, live "working" spinner.
- Evidence pack: one `FactCard` per fact with its source chip, its clickable locator, the
  time, **whether code or the model read it**, and the portal screenshot as a thumbnail.
- Proposed decision with the confidence bar and the written checklist under it; the refusal
  gets its own card with the full "here is where I looked" list, every dead end included.

### 4c — decide + policies + counters

- `DecideBar`: Approve / Reject / Edit. Approve means "do what Tieout proposed" and the engine
  resolves it; Edit opens a picker for the other three `DecidableAction`s plus the note that
  ends up on the rule. The approver's name comes from the control bar and is shown next to
  the buttons, so nobody presses Approve without seeing whose name goes on the policy.
- `PolicyCard`: id, version, active/superseded, the condition, the action, **the approver and
  the date**, what it was learned from, and what has cited it. The condition is rendered from
  the `PolicyCondition` fields in the order `describe()` writes them — that method is a plain
  Python method and is not on the wire.
- Counters are six real figures from `GET /metrics`, refetched whenever a run or a decision
  finishes. Empty still reads "—", never `0`.
- **The moment works.** After one approval, working E2 turns its queue row into
  **"cleared by SHORT-SHIP-01 v1 · Chris, Controller"** and human touches stays at 1.

### 4d — polish

- Loading, empty and error states everywhere; `ErrorBanner` shows the API's own words.
- Reset button (`POST /reset`) puts the world, the memory, the saved session and the
  screenshots back and reselects E1.
- `animate-land` — one short arrival for a fact, an auto-clear row and a newborn rule, with a
  `prefers-reduced-motion` escape.
- The pack reads as one document and follows itself: the newest fact while evidence lands,
  then the verdict from its first line the moment there is one.
- `devIndicators: false` — Next's dev badge sat exactly on the approver field, and this screen
  gets recorded from `next dev`.

### The live browser panel (asked for on top of the plan)

A fourth zone. The engine's Playwright session is a real Chromium on the same machine, and
before this it was invisible unless you ran `HEADLESS=0` and filmed a second window. The panel
draws a browser chrome, puts the fact's own locator in the address bar, and shows the
screenshot the agent filed as evidence — updating as each portal fact arrives on the stream.
Clicking a fact card's thumbnail pins that one.

**One route was added to the API to make this possible**, which is the ninth route on a plan
that said eight. `Fact.screenshot` is an absolute path on the engine's machine
(`C:\Users\…\.tieout\screenshots\E1-PO-1042.png`), and a browser cannot open one.
`GET /screenshots/{name}` serves those bytes and nothing else: the name is reduced to its last
component and must resolve directly inside the screenshot folder. No logic went into `api/`;
it is a `FileResponse` over `engine.sources.portal.screenshot_dir()`, and
`backend/tests/test_api.py` covers both the happy path and four escape attempts.

## Next action

Nothing in this folder. Phase 4 is done and hardened, and the README is written. What is left
is Rohit's: the video and the Discord post.

## Decisions made

- One page, as planned, but **four zones instead of three**: the live browser sits above the
  policies in the right column. The three-column diagram in `CLAUDE.md` predates the browser
  panel being asked for.
- **Approve/Reject/Edit is three buttons, not a form.** The one human touch should cost one
  click; Edit is the escape hatch and hides until it is wanted.
- **The live event trail disappears when the run ends.** While it is happening it is the whole
  point ("signed in to VendorLink as ap-bot@kestrelmfg.com"); afterwards every line of it is
  in the facts and the checklist, and the pack is what a person reads.
- **The rationale is never truncated.** It is the audit trail; a `line-clamp` on it would have
  bought two visible fact cards and cost the thing the project is about.
- `Screenshot.tsx` is the only `<img>` on the desk and the only eslint-disable. `next/image`
  optimises and caches remote files, and both are wrong for a live artefact of the run
  happening on screen.
- Phosphor is installed now that there is something for an icon to do (source chips, ticks,
  the browser chrome, the rule stamp). Still no chart library and no state library.
- Times are wall-clock (`en-GB`, 24h) because the reader is watching it happen; dates are
  `6 Sept 2026` because that is what goes on a rule.

## How to run it

```bash
python -m tieout.api            # :8700 — starts the fake company too
cd desk && npm run dev          # :3000 (or the next free port — check the log)
```

Then, on the screen and nowhere else: **Work E1 → Approve → select E2 → Work E2 → select E5 →
Work E5.** `NEXT_PUBLIC_API_BASE` moves the API off `http://localhost:8700`.

## Blockers

None.

## Session log

- **2026-09-06 (S5, harden + ship)** — five full passes of the four beats through the screen,
  driven by a throwaway Playwright harness against a live API and a real Chromium. Fixed the
  two staleness bugs above and added the "Still open" counter. Typecheck, lint and build clean.
- **2026-09-03** — folder created, plan written. No code.
- **2026-09-05** — 4a built: Next 16.3.4 skeleton, design system ported from Cairn with new
  fonts and a new accent, empty four-zone layout, typed API stubs. Verified with a real
  `next dev`, `tsc --noEmit`, `eslint`, `next build` — all clean.
- **2026-09-06** — 4b, 4c and 4d built, plus the live browser panel. The types were
  reconciled against the real `engine/models.py`. The four beats were driven from the screen
  three times end to end against a live API and a real Chromium on the real portal, with
  screenshots checked each time; the counters on screen are the ones `GET /metrics` returns.
  Added `GET /screenshots/{name}` to the API — the only backend change — with a test.
