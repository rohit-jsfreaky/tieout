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

- **4a, 4b, 4c and 4d are DONE, and the desk has since been rebuilt as a proper app**
  (2026-09-06, S8): shadcn/ui on Base UI, a sidebar, and five real views instead of three
  panels with no navigation. `npm run typecheck`, `npm run lint` and `npm run build` are clean.
- **No mock mode anywhere.** Every figure on the screen came out of `GET /metrics`, `GET /queue`,
  `GET /policies` or the SSE stream in that session. `lib/api.ts` is still the only file that
  fetches or opens a stream.
- Verified by driving the real screen end to end (a throwaway Playwright script, since deleted)
  against a live `python -m tieout.api`, at 1600×1000 and again at 700×900, with **zero page
  errors**. All four beats passed from the screen alone and the counters read
  **5 exceptions · 1 human touch · 1 auto-cleared · 1 refused · 16 evidence items**.

## Done

### The rebuild — sidebar, five views, shadcn/ui (2026-09-06)

The problem it fixes: the old screen was three columns with no navigation and no instructions.
A judge with three minutes did not know where to click.

- **`npx shadcn@latest init`** on the existing Next 16 / Tailwind v4 project. Registry `@shadcn`,
  style `base-nova`, base **Base UI** (so custom triggers use `render`, not `asChild`).
  Components added: sidebar, card, table, badge, separator, button, input, dialog, sheet, tabs,
  alert, empty, skeleton, sonner, tooltip, scroll-area, field, select, label, spinner.
  `npx shadcn@latest docs <component>` was read for each one before it was used.
- **Icons are Phosphor, and only Phosphor.** `components.json` has `iconLibrary: "phosphor"`, so
  the CLI rewrote every registry icon on the way in (`XIcon`, `CaretDownIcon`, `SidebarIcon` …
  are all real `@phosphor-icons/react` v2 aliases — checked against `dist/csr/*.d.ts`, not
  assumed). `lucide-react` and `next-themes` were uninstalled; nothing imports either.
- **The design system survived.** `app/globals.css` still owns Fraunces/Geist/Geist Mono, the
  4px radius ladder, `corner-shape: squircle`, `animate-land` and the four inset-shadow
  utilities. shadcn's semantic layer is *mapped onto* Tieout's palette in one `:root` block —
  `--background` is white, `--foreground`/`--primary` are ink, `--muted-foreground` is the muted
  ink, `--muted`/`--accent`/`--secondary` are mist, `--ring` is ledger blue. The result still
  looks like Tieout.
- **Five views, one sidebar.** Queue (default) · Exception · Policies · Audit · Settings, with
  live counts on the sidebar rows.
- **The guide card.** Dismissible, on the Queue view, three numbered steps — Work E1, Approve it,
  Work E2 — and a button that works the next untouched exception. This was the point of the
  session.
- **Audit is new.** Every fact, decision and learned rule across every exception, in time order,
  with source, link, screenshot marker, who read it and when. It is assembled in `useDesk` by
  flattening the packs the API returns; nothing on it is computed here.
- **Settings is new.** The approver's name, the API base URL (stored in `localStorage`, so the
  desk can be pointed at an API on another machine without a rebuild), and Reset behind a
  confirmation dialog.
- **`sonner` toasts** for the two moments worth announcing: a rule being learned, and an
  exception clearing itself.
- `BrowserPanel` was kept exactly as it was, inside a Card in the Exception view's sticky right
  column.

### 4b — queue + evidence pack

- `lib/api-types.ts` **written against the real backend**, mirrored from `engine/models.py` and
  `engine/events.py` in the same order, because `api/schemas.py` re-exports them unchanged.
  Pydantic `computed_field`s (`exposure`, `short_pct`, `Policy.ref`, …) are on the wire, so the
  desk never recomputes a number the engine published. There is no `exception_class` (it is
  `kind`), no `Refusal` object (a refusal is a `Decision` with `action: "refuse"`), and the queue
  is `{count, exceptions: QueueRow[]}`, not a bare array.
- `lib/api.ts` — nine routes and one stream. `ApiError` carries FastAPI's own `detail`, so a
  409 reads "an investigation is already running on E1" rather than "Failed to fetch".
  `streamException` subscribes to all twelve `EventKind`s plus `done`, because sse-starlette
  names each message by the event's own `kind` — **there is no `message` listener to hang
  anything on**, which is the one thing that will silently break if someone adds a kind.
- `lib/useDesk.ts` — the whole state. Live events are merged into the fetched pack by id
  (facts) and by `source|action|locator|at` (steps), so the same list works mid-run and at
  rest with no second code path.
- Evidence: one `FactCard` per fact with its source chip, its clickable locator, the time,
  **whether code or the model read it**, and the portal screenshot as a thumbnail.

### 4c — decide + policies + counters

- `DecideBar`: Approve / Reject / Edit, **with the approver field on the card itself** — nobody
  presses Approve without seeing whose name goes on the rule. Approve means "do what Tieout
  proposed" and the engine resolves it; Edit opens a Select of the other three
  `DecidableAction`s plus the note that ends up on the rule.
- `PolicyCard`: id, version, active/superseded, the condition, the action, **the approver and
  the date**, what it was learned from, and what has cited it. The condition is rendered from
  the `PolicyCondition` fields in the order `describe()` writes them — that method is a plain
  Python method and is not on the wire.
- Counters are six real figures from `GET /metrics`, refetched whenever a run or a decision
  finishes. Empty still reads "—", never `0`.
- **The moment works.** After one approval, working E2 turns its queue row into
  **"cleared by SHORT-SHIP-01 v1 · Chris, Controller — nobody was asked"** and human touches
  stays at 1.

### 4d — polish

- Loading (`Skeleton`), empty (`Empty`) and error (`Alert`) states everywhere; the error shows
  the API's own words.
- Reset (`POST /reset`) puts the world, the memory, the saved session and the screenshots back
  and reselects the first exception.
- `animate-land` — one short arrival for a fact, an auto-clear row and a newborn rule, with a
  `prefers-reduced-motion` escape.
- `devIndicators: false` — Next's dev badge sat exactly on the approver field, and this screen
  gets recorded from `next dev`.

### The live browser panel

The engine's Playwright session is a real Chromium on the same machine, and before this it was
invisible unless you ran `HEADLESS=0` and filmed a second window. The panel draws a browser
chrome, puts the fact's own locator in the address bar, and shows the screenshot the agent filed
as evidence — updating as each portal fact arrives on the stream. Clicking a fact card's
thumbnail pins that one.

**One route was added to the API to make this possible**, which is the ninth route on a plan
that said eight. `Fact.screenshot` is an absolute path on the engine's machine
(`C:\Users\…\.tieout\screenshots\E1-PO-1042.png`), and a browser cannot open one.
`GET /screenshots/{name}` serves those bytes and nothing else: the name is reduced to its last
component and must resolve directly inside the screenshot folder. No logic went into `api/`;
it is a `FileResponse` over `engine.sources.portal.screenshot_dir()`, and
`backend/tests/test_api.py` covers both the happy path and four escape attempts.

## Next action

Nothing in this folder. Phase 4 is done, hardened, and rebuilt as a proper app, and the README
is written — though the README predates the sidebar, so its description of the screen is worth
a second look. What is left is Rohit's: the video and the Discord post.

## Decisions made

- **Views are state, not routes.** `desk/CLAUDE.md` said one page and no second page, and there
  is a practical reason to keep it that way: `useDesk` stays mounted for the life of the screen,
  so an SSE run keeps streaming while somebody wanders off to read the rules it just learned.
  The cost is that the browser Back button does not step between views.
- **The radius ladder was not touched.** shadcn's components ask for `rounded-lg` on controls and
  `rounded-xl` on cards; under Tieout's 4px ladder those are 18px and 24px rather than shadcn's
  10px and 14px. Everything on the screen shares one ladder, and the nesting order is still
  right (control inside card), so the ladder stayed exactly as the design system defines it.
- **`--color-muted` had to move.** Tieout used `muted` for an *ink*; shadcn uses it for a
  *surface*. The muted ink is `text-muted-foreground` now, and every call site was changed.
  `ink`, `faint`, `mist`, `soft` and `ledger` keep their Tieout names — none of them collide.
- **`--destructive` is defined but never used.** Tieout has no red state: a refusal is an
  outcome, not an error, and Reject is an outline button. The token exists so the primitives are
  whole.
- **Two variants were added to registry components**, both for the accent: `Button variant="ledger"`
  (the one filled accent button on the screen — Approve) and `Badge variant="ledger"` (auto-cleared,
  active rule, "read by the model"). `SidebarMenuButton`'s hover was also split from its active
  state, which the registry copy had sharing one token, so you can see which view you are on.
- **`hooks/use-mobile.ts` was rewritten** as a `useSyncExternalStore` read. The registry version
  sets state inside an effect, which this project's lint rejects.
- **Approve/Reject/Edit is three buttons, not a form.** The one human touch should cost one
  click; Edit is the escape hatch and hides until it is wanted.
- **The verdict sits above the evidence.** The reader has to decide and then check, so the
  proposal and the Approve button are near the top and the facts run underneath in the order
  they landed. The rationale is never truncated — it is the audit trail.
- **The live event trail disappears when the run ends.** While it is happening it is the whole
  point ("signed in to VendorLink as ap-bot@kestrelmfg.com"); afterwards every line of it is in
  the facts and the checklist, and the pack is what a person reads.
- `Screenshot.tsx` is the only `<img>` on the desk and the only eslint-disable. `next/image`
  optimises and caches remote files, and both are wrong for a live artefact of the run
  happening on screen.
- Times are wall-clock (`en-GB`, 24h) because the reader is watching it happen; dates are
  `6 Sept 2026` because that is what goes on a rule.

## How to run it

```bash
python -m tieout.api            # :8700 — starts the fake company too
cd desk && npm run dev          # :3000 (or the next free port — check the log)
```

Then, on the screen and nowhere else, following the guide card on the Queue view:
**Work E1 → Approve → Work E2 → open E5 → Work E5.** The API address can be changed on the
Settings view, or baked in with `NEXT_PUBLIC_API_BASE`.

## Blockers

None.

## Known environment quirk (not an app bug)

The page **does not hydrate inside AO's desktop Browser panel** — clicks do nothing there and
the sidebar never appears, with no page errors reported. The same URL in a real Chromium
hydrates and works at both 1600px (sidebar pinned) and 700px (sidebar in a Sheet behind the
toggle), verified twice with zero console errors. Record the demo from a normal browser.

## Session log

- **2026-09-06 (S5, harden + ship)** — five full passes of the four beats through the screen,
  driven by a throwaway Playwright harness against a live API and a real Chromium. Fixed the
  two staleness bugs above and added the "Still open" counter. Typecheck, lint and build clean.
- **2026-09-03** — folder created, plan written. No code.
- **2026-09-05** — 4a built: Next 16.3.4 skeleton, design system ported from Cairn with new
  fonts and a new accent, empty four-zone layout, typed API stubs. Verified with a real
  `next dev`, `tsc --noEmit`, `eslint`, `next build` — all clean.
- **2026-09-06** — 4b, 4c and 4d built, plus the live browser panel. The types were
  reconciled against the real `engine/models.py` (4a had guessed them from `backend/PLAN.md`
  and got several wrong). The four beats were driven from the screen three times end to end
  against a live API and a real Chromium on the real portal, with screenshots checked each
  time. Added `GET /screenshots/{name}` to the API — the only backend change — with a test.
- **2026-09-06 (S8, `desk`)** — rebuilt as a proper app: shadcn/ui on Base UI, a sidebar and
  five views (Queue, Exception, Policies, Audit, Settings), a dismissible three-step guide card
  on the queue, toasts, and a Settings view that can repoint the API. Phosphor everywhere, no
  Lucide, design system intact. Driven end to end against the live API twice; typecheck, lint
  and build clean.
