# PROGRESS — desk/

> Working memory for this folder. Read first, update before ending every session.

## Current state — 2026-09-06 (S9, the readability pass on the Exception view)

**Polish only — no new behaviour, no backend change.** The view was correct and unreadable at a
glance: a thumbnail browser in an empty column, seven full-size fact cards, a column of unnamed
numbers, a grey wall of rationale, and every block the same size. Six fixes, in the order Rohit
listed them. `npm run typecheck`, `npm run lint` and `npm run build` are clean, and the whole
thing was driven in a real Chromium at 1600×1000 against the live API — E1 (recorded), E2
(auto-cleared), E5 (refused) and E3 (never worked) — with **no page errors and no console
errors**.

- **The live browser fills its column.** The right column went 25rem → 30rem, the panel lost its
  inner padding so the chrome and the page go edge to edge inside the card, and the card is no
  longer a fixed 28rem box: it is as tall as the screenshot it is showing
  (`min-h-[15rem] max-h-[calc(100svh-16rem)]`), because a band of empty grey under a screenshot
  reads as something that failed to load. It stays `xl:sticky xl:top-0`, so the portal page holds
  still while the evidence scrolls. With nothing to show it is a Phosphor `Browser` mark on a
  `surface` disc over the sentence explaining why a real browser is being driven at all.
- **A fact is one line now.** `FactRow` (new) replaces `FactCard` (deleted): kind, the statement
  clamped to one line, a camera mark if there is a screenshot, the time. Click it and the full
  text, the locator, who read it and the screenshot unfold underneath. `EvidenceList` (new)
  groups **consecutive** facts by source — "Inbox · 3 facts" over three lines instead of three
  identical boxes. The grouping is only ever over neighbours: if the agent goes back to the ERP
  after the portal that is a second visit and gets its own heading, because the order is part of
  the evidence. Seven facts now cost about a third of the height they did.
- **The weights are named.** `ChecklistLines` has a `check` / `weight` header, and `weight`
  carries a shadcn `Tooltip`: "What each check is worth. The weights that passed add up to the
  confidence." No bare `0.30` on the screen any more.
- **`WhyThisDecision` (new)** puts the rationale on a toggle at 13px instead of 12px faint —
  open on a decision somebody still has to make, closed on one that cleared itself. It is never
  truncated and never paraphrased; it is just not shouted at a reader who did not ask.
- **One badge per view.** `StatusBadge` in the exception header is the only badge on the page
  now. `DecisionCard` and `RefusalCard` dropped theirs, and the action moved into the card as a
  named figure — `action Short-pay · pay $1,757.50` — because "Short-pay" is what Tieout wants
  to DO, not where the invoice stands.
- **The spine, by size and spacing only, no new colour.** The decision's summary is Fraunces at
  19px and its card carries a wider `--card-spacing`; the invoice strip above it dropped to 16px
  `size="sm"`; the evidence heading is an 11px eyebrow like the decision's own. Blocks are
  `gap-5` apart, rows inside them `gap-1.5`. E2 now reads in one screen: what broke, what was
  decided, the rule and the name that decided it, the trail, and the portal page beside it.
- `FigureRow` / `Figure` (new) is the `label value` pair the invoice strip already used, now
  shared with the decision card. `hairline-top` joined `hairline` in `globals.css`.

## Earlier — 2026-09-06 (S7, authority wired into the shadcn desk)

**Approval authority is on the real screen now.** S6 built it on the old three-panel
components; `master` had already replaced those with the shadcn rebuild, so the merge kept the
types and lost the UI. This session put it back on the components that actually render, and
`AuthorityNote` was rewritten as a shadcn `Alert` rather than a hand-rolled div.

Driven end to end against a live `python -m tieout.api` and a real Chromium — reset, the four
beats, the block, and the CFO clearing the same pack — **21 of 21 checks pass with no page
errors and no console errors**. `npm run typecheck`, `npm run lint` and `npm run build` clean.

- **`useDesk.approver` is an `Approver { name, role }`**, never a string somebody typed. It
  also exposes `authority` (the matrix, read once from `GET /authority`), `authorityNote` (the
  engine's own sentence about where a real matrix comes from) and `approverSeat` — the
  approver's row in that matrix, `null` until it lands, because unknown and unlimited are not
  the same thing. `decide` sends `by` and `role` as two fields; the engine never has to guess.
- **`RoleSelect` (new)** is the seat control, on the decide bar and on Settings. Its options
  are the rows of the matrix and nothing else — "Controller · $10,000.00" — so the screen can
  never offer a seat or a limit the engine did not publish. Before the matrix lands it holds
  one option and is disabled.
- **Settings has the matrix**, as a `Table` straight off `GET /authority`, the approver's own
  row highlighted, with the API's own note as the card description. No number in this folder
  is typed by hand.
- **`AuthorityNote` is a shadcn `Alert`** when the decision authorises more than the seat may
  sign: *"$12,750.00 is above a Controller's $10,000.00 limit. This needs the CFO."* plus what
  happens next. Under the limit it is a quiet line, not an alert — "Authorises $1,757.50 for
  payment — Controller authority. As a Controller you may sign up to $10,000.00." Both numbers
  are off the wire (`decision.amount_for_authority`, the seat's row). `aboveAuthority()` is the
  single comparison, so the alert and the disabled button can never disagree.
- **Approve is disabled above the limit.** Reject needs no spending authority and Edit can
  resolve to a smaller payment, so both stay live — and if you insist through Edit, the engine
  escalates and the card reads **"Above their authority — escalated"** with the engine's own
  sentence on it. An escalation is deliberately not "settled": the decide bar stays open,
  switch the seat to CFO and the same evidence pack goes through. That is the fifth beat.
- **E5 reads as both at once**, which was the point: "NOT CONFIDENT — YOU DECIDE" with 0 of 4
  checks and every dead end listed, and directly under it the alert saying the payment is above
  a Controller's authority. Two independent reasons this cannot end at this desk.
- **`PolicyCard` shows the inherited ceiling** — "Chris, Controller (limit $10,000.00) ·
  6 Sept 2026" — and "payment ≤ $10,000.00" sits in the rule's When list next to the tolerance
  and the exposure. It is not part of `PolicyCondition` (`policy.covers` checks it separately)
  but it stops the rule exactly like they do, so it is read exactly like them.
- **`StatusBadge` knows `escalated`** ("Above their limit"), which the rebuild's `Record` had
  been missing since the type gained the state.
- `format.ts` gained `roleArticle` — "an AP Clerk", "a Controller". Grammar, not policy; the
  engine keeps the same little table for the sentences it writes.

### Known, not fixed

A `~/.tieout` store written by a build from **before** approval authority makes `GET /metrics`
and `GET /policies` return 500 — the old policy rows have no `approved_role` and pydantic
refuses them. `POST /reset` clears it, which is what the desk's Reset button does. It cannot
happen to a fresh clone; it happened once on this machine.

## Earlier — 2026-09-06 (S6, approval authority limits, on the pre-rebuild components)

**The approver is no longer just a name.** The control bar has a name AND a seat, and the seat
carries a limit. `npm run typecheck`, `npm run lint` and `npm run build` are clean, and the
whole thing was driven end to end against a live `python -m tieout.api` and a real Chromium
with **no page errors**.

- **`ControlBar` is name + role.** The role is a `<select>` populated from `GET /authority` —
  the desk never lists a seat or a limit the engine did not publish. Next to it: "may approve
  $10,000.00 · that limit goes on every rule this approval creates". Before the matrix lands
  the limit shows `—`, not "no limit", because unknown and unlimited are not the same thing.
- **`AuthorityNote` (new)** sits on both the decision card and the refusal card. It says what
  signing this off would authorise and who may do it, and when the amount is above the seat's
  limit it says so plainly and warns that approving will be blocked. Both numbers are off the
  wire: `decision.amount_for_authority` is published by the engine on every decision, the
  limit is the row for this seat in the matrix. The `>` here only decides what to *say* —
  **the engine blocks server-side whatever this screen believes.**
- **E5 now shows both reasons at once**, which was the point: "Not confident — you decide"
  with 0 of 4 checks, and directly under it "$12,750.00 is above your $10,000.00 limit as
  Controller. This needs the CFO."
- **A blocked approval is a state on the card, not an error banner.** `DecisionCard` reads
  "Above their authority — escalated" and shows the engine's own sentence. An escalation is
  deliberately **not** treated as settled, so the decide bar stays open: change the seat to
  CFO and approve, and the very same pack goes through. That is the demo.
- **`PolicyCard` shows the ceiling** — "Chris, Controller (limit $10,000.00) · 6 Sept 2026" —
  and "payment ≤ $10,000.00" sits in the rule's When list next to the tolerance and the
  exposure, because it is enforced exactly like they are.
- `api-types.ts` mirrors the new engine shapes: `Role`, `Decision.approved_role` /
  `amount_for_authority` / `authority_needed`, `Policy.approved_role` / `authority_ceiling`,
  the `escalate` action, the `escalated` status and the `escalated` event kind (added to
  `EVENT_KINDS`, which is the list the stream subscribes by — miss it and the message is
  silently dropped). `api.ts` gained `getAuthority()`; `format.ts` gained `limitLabel`, which
  is the one place that knows `null` means no limit rather than a limit of zero.
- `useDesk`'s `approver` is now `{ name, role }` and it exposes `authority` (the matrix, read
  once) and `approverLimit` (a lookup in it, never a number this file made up).

## Earlier — 2026-09-06 (after S5's hardening pass)

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

Nothing in this folder. Phase 4 is done, hardened, rebuilt as a proper app, carries the authority
control on every view that needs it, and has had its readability pass. The README predates the
sidebar and the matrix, so its description of the screen is worth a second look. What is left is
Rohit's: the video and the Discord post.

## Decisions made

- **The source chip sits on the group heading, not on every fact row.** The brief asked for the
  chip on the row AND for three vendor emails to read as "Inbox · 3 facts"; repeating the chip
  three times under a heading that already says Inbox is the wall the brief was complaining
  about. So the chip states the source once per visit and the rows under it carry the fact.
- **The browser card is as tall as its screenshot, not as tall as the column.** A fixed-height
  panel gave a big page a scrollbar and a small one 400px of empty grey. It has a floor
  (15rem, for the empty state) and a ceiling (the viewport), and sits between them.
- **`WhyThisDecision` is keyed on `decision.auto`.** `defaultOpen` is only an initial value, and
  the same card stays mounted while an exception goes from proposed to recorded to cleared — the
  key makes the default apply again when the kind of decision changes underneath it.
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

- **2026-09-06 (S9, `readability`)** — the six-point polish pass on the Exception view: the live
  browser filling its column and sticky, facts as one-line rows grouped by visit, the weight
  column named with a tooltip, the rationale behind a "Why this decision" toggle, one status
  badge per view, and a size-and-spacing spine. `FactRow`, `EvidenceList`, `WhyThisDecision` and
  `FigureRow` are new; `FactCard` is gone. Checked in a real Chromium against the live API on
  E1, E2, E5 and E3 by a throwaway Playwright script (since deleted, and it lived outside the
  repo): no page errors, no console errors. Typecheck, lint and build clean.
- **2026-09-06 (S7, `authority on the shadcn desk`)** — rewired approval authority onto the
  rebuilt desk: `Approver` in `useDesk`, `RoleSelect` off the matrix, the matrix table on
  Settings, `AuthorityNote` as a shadcn `Alert`, Approve disabled above the limit, the
  escalated state on `DecisionCard` and `StatusBadge`, and the ceiling on `PolicyCard`. Driven
  through reset → E1 → approve → E2 → E5 → escalate → CFO → Settings by a throwaway Playwright
  harness (since deleted): 21 of 21 checks, no page errors. Typecheck, lint and build clean.
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
