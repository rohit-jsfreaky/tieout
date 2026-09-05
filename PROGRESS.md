# PROGRESS — Tieout (root live state)

> Read this first, every session. Update it before ending the session.
> Per-folder detail: `backend/PROGRESS.md`, `desk/PROGRESS.md`.

## Current state — 2026-09-06 (S5, `harden + ship`)

- **Phase 5 is DONE except the video and the Discord post.** No code left, no open bugs.
  - **`README.md` is written**, to the hackathon checklist. Every number in it came out of a
    run on this machine and the command that produces it is printed next to it. The only
    figures not measured here are the AP industry statistics, and the README says so.
  - **`tieout reset` + `tieout demo`, five times from cold.** Runs 2–5 were byte-identical to
    each other; run 1 differed only in the E1 rationale paragraph, which is model prose.
    Every reproducible thing — facts, steps, checklists, the rule, the citation, all twelve
    counters — was identical in all five. ~22 s a run.
  - **`tieout work E3` and `tieout work E4` after a reset**: both propose at 100% confidence
    (approve, and attach_po).
  - **The four beats through the desk, five times** against a live `python -m tieout.api` and
    a real Chromium: identical counters every round, no page errors, and the desk's counters
    now match what `tieout demo` prints exactly (16 evidence items, 3 screenshots).
  - **`pytest backend/tests` 46 green, ruff clean; desk typecheck, lint and build clean.**
- **Rohit's two findings are fixed.**
  - E4's rationale said "Exception E4 is invalid because the supplier confirmed there is no
    order number" — backwards. `RATIONALE_SYSTEM` in `engine/model.py` now says the exception
    is an established finding from a deterministic match, forbids the valid/invalid framing
    and fixes the order of the paragraph. It now reads "Invoice INV-3039 ... did not tie out
    because it lacked an order number". Written up in `RESEARCH.md` as gotcha 5.
  - **`open_not_worked` is a new counter** — the exceptions nobody has picked up yet. It is on
    `Metrics`, in `tieout metrics` and `tieout demo` ("Open, not yet worked"), on the desk
    ("Still open"), and asserted in `test_api.py` and `test_policy_loop.py`.
- **Two bugs the five desk passes found, both in `desk/lib/useDesk.ts`, both fixed:**
  1. **The counter strip could read all zeros after Reset.** `loadBoard` asked for `/queue`,
     `/policies` and `/metrics` in one `Promise.all` — but `/queue` is the call that runs the
     three-way match and fills the store, so `/metrics` could answer from an empty one. The
     queue is now read first, the counters after it.
  2. **The counters lagged a whole beat behind the screen** — "Not confident" on screen next
     to "Refused 0" — because a run cleared `pending` before its refetch landed. `pending` now
     clears only when the board and the pack have come back.
- **Left for Rohit:** the demo video and the Discord post. Nothing else.

## Earlier today — 2026-09-06

- **Phase 4 (desk) is DONE. All four phases are done.** Its finish line passes: **the four
  beats can be driven from the screen with nothing else open** — no terminal, no curl, no
  mock data. `npm run typecheck`, `npm run lint` and `npm run build` are clean.
  Detail in `desk/PROGRESS.md`.
  - Work E1 → the facts land live, each with its source chip, its link, the time and whether
    code or the model read it; the portal fact carries its screenshot.
  - Approve as **Chris, Controller** → `SHORT-SHIP-01 v1` appears on the right with his name
    and the date on it.
  - Work E2 → its queue row reads **"cleared by SHORT-SHIP-01 v1 · Chris, Controller"** and
    human touches stays at **1**. That row is the product.
  - Work E5 → **"Not confident — you decide"**, 0 of 4 checks, and the full list of the eight
    places it looked.
  - **A live browser panel** (asked for on top of `desk/PLAN.md`) shows the VendorLink page
    the agent is reading, as each portal screenshot arrives on the stream — so the sign-in
    happens inside the product instead of in a second window.
  - Counters from a real run: **5 exceptions · 1 human touch · 1 auto-cleared · 1 refused ·
    12 evidence items · 3 screenshots.** The evidence count moves run to run (10–16) because
    how many facts the model pulls out of the vendor's email is not deterministic; every
    reproducible number — the rule, the citation, the touches — is identical every time.
- **The API has a ninth route.** `GET /screenshots/{name}` serves the PNGs a portal `Fact`
  points at, because an absolute path on this machine is not something a browser can open.
  It holds no logic and it has a test. That was the one open call for Rohit in the note
  below; it is now closed. `pytest backend/tests` is **46 green**, ruff clean.
- **Left for Rohit:** the README, the demo video, and the Discord post. No code left.
- **Phase 3 (api) is DONE.** Its finish line passes: **the four beats run through `curl`
  alone**, against a live `python -m tieout.api` on :8700, with the SSE stream showing the
  VendorLink sign-in as it happens. Eight routes, no logic in `api/`. `pytest backend/tests`
  is green — 45 tests — and ruff is clean. Detail in `backend/PROGRESS.md`.
  - `curl -N :8700/exceptions/E1/events` shows every lookup step and every Fact live,
    including "signed in to VendorLink as ap-bot@kestrelmfg.com" and the screenshot path.
  - `POST /exceptions/E1/decide {"action":"approve","by":"Chris, Controller"}` returns the
    new rule `SHORT-SHIP-01 v1` with the name and date on it.
  - `POST /exceptions/E2/work` streams `auto_cleared`, citing that rule and Chris, with no
    sign-in — the saved session was reused. `POST /exceptions/E5/work` streams `refused`.
  - `GET /metrics` returns the same numbers `tieout demo` prints: 5 found, 1 human touch,
    1 auto-cleared, 1 refused, 16 evidence items, 3 screenshots, 1 policy, 1 citation.

## Earlier — 2026-09-05

- **Phase 1 (world) is DONE.** Its finish line passes: one command starts the ERP (:8701),
  the VendorLink portal (:8702) and the AP inbox (:8703); `curl :8701/invoices` returns 40;
  a real browser signs into the portal and reads "95" off delivery note DN-1042;
  `tieout reset` puts the world back to the seed. Detail in `backend/PROGRESS.md`.
- **Phase 2 (engine) is DONE.** Its finish line passes: `tieout demo` runs all four beats
  from a fresh reset, and `pytest backend/tests -q` is green — 38 tests, three of which
  drive a real Chromium against the real portal. ruff clean.
  - `tieout match` finds exactly the five seeded exceptions with a real three-way match and
    never reads the seed's answer table (a test enforces that).
  - `tieout work E1` gathers ERP facts, the vendor email and the portal delivery note with a
    screenshot, and proposes a short-pay at 100% confidence.
  - `tieout decide E1 approve --by "Chris, Controller"` creates `SHORT-SHIP-01 v1`, stamped
    with the name and the date; `tieout work E2` is then **auto-cleared, citing that rule and
    Chris**, without a login — it reuses the saved VendorLink session.
  - `tieout work E5` **refuses** and lists the eight places it looked.
  - Real numbers from the run: 5 found, 1 human touch, 1 auto-cleared, 1 refused,
    16 evidence items, 3 screenshots, 1 active policy, 1 citation.
- **Two model findings from Phase 2 still need to go into `RESEARCH.md` by hand** (that file
  has uncommitted edits in the main checkout, so S2 left it alone): `enable_thinking: false`
  makes `glm-4-7-flash` answer in 2.9 s instead of 19.7 s, and empty content is now retried
  with a doubled token budget rather than a longer wait. Both written up in
  `backend/PROGRESS.md` -> "Model notes".

## Before the window — 2026-09-03

- **Build window is open.** Phase **4a is done** (see `desk/PROGRESS.md`); Phases 1–3
  (`backend/`) are in flight in their own AO sessions. The desk cannot go past 4a until the
  Phase 3 finish line passes.
- Setup notes below are kept for the record.
- Registered on Luma, approved, Discord joined (2026-09-03).
- Idea locked via the hackathon_ideas pipeline (that repo's `IDEAS-LOG.md`, entry 2026-09-03).
  Discord read: nobody has announced an idea; judge is a 22-time winner; his stated priority
  is the self-improving loop and the engineering.
- Scaffold + plans written 2026-09-03. **No code. None allowed before the window.**
- Name checked: `tieout.com` does not resolve; GitHub has 34 small unrelated repos.

## ▶ START HERE (Phase 0, before Saturday)

1. Install AO (Windows build from the GitHub releases page). Open a throwaway repo in it.
   Run ONE full session: create → work → follow-up message → close. Note anything confusing in
   `RESEARCH.md` so hour 1 on Saturday is not spent learning the IDE.
2. ~~Model provider~~ **DONE 2026-09-04.** TensorMux account created, key in `.env`,
   $5/$5 credit confirmed, live call returned 200. Model: `gemma-4-31b`. See RESEARCH.md —
   including two gotchas (it fences JSON, and it invents years).
3. `playwright install chromium`. Node 20+ and Python 3.11+ ready.
4. 30 minutes: read about the 3-way match, short-ship, price variance, non-PO invoices. Put
   five lines of notes in `RESEARCH.md` → "Finance notes".
5. Rohit creates the empty public repo on GitHub (MIT). Nothing pushed until the window.

## Then, at 21:30 IST Saturday

Open AO. Session S1 on the `world` module. Read `backend/PLAN.md`. Go.

## Open questions

- OpenRouter model ID for the three LLM jobs (facts from text, decision rationale, rule
  generalisation). Cheap and fast beats clever here — every call is on the demo path.
- Does AO's session/worktree flow work cleanly on Windows with a monorepo of four folders?
  Find out in the practice session, not on Saturday.
- Neatlogs: worth wiring for the video? Founder is in the Discord offering help. Optional —
  only if Phase 4 finishes early.
- Team name for the Discord post: "Tieout" (solo).

## Session log

- **2026-09-06 (S5, `harden + ship`)** — five cold `tieout demo` runs, five passes through the
  desk, `work E3`/`work E4`, the no-key path, and the README. Fixed Rohit's two findings and
  two staleness bugs the repeated desk runs exposed. Added `open_not_worked` end to end.
  46 tests green, ruff clean, desk typecheck/lint/build clean. The two Phase 2 model findings
  and a new fifth one are now in `RESEARCH.md`.
- **2026-09-06 (S4, `desk`)** — Phase 4 finished inside the window: steps 4b, 4c and 4d,
  plus a live browser panel that was not in the plan. The desk's types were reconciled
  against the real `engine/models.py` (4a had guessed them from `backend/PLAN.md` and got
  several wrong). The four beats were driven from the screen end to end three times
  against a live API and a real Chromium on the real portal. The API gained its ninth
  route, `GET /screenshots/{name}`, with a test — the only backend change.
- **2026-09-03** — event researched, idea picked, Discord read, scaffold + plans written.
- **2026-09-04** — structure simplified to TWO folders: `backend/` (one Python project with
  world/engine/api modules) and `desk/`. Was three separate Python projects; now one
  pyproject, one venv, one install. Phases and finish lines unchanged.
  AO v0.12.10 confirmed (Windows .exe, 126 MB). TensorMux (sponsor) gives $5 free with no
  card and is OpenAI-compatible — use it as the model provider, OpenRouter $3 as backup.
- **2026-09-05** — S4 / Phase **4a done** (desk skeleton + design system). Next 16.3.4,
  Tailwind v4, Cairn's inset-shadow/squircle system ported with Tieout's own fonts (Fraunces
  + Geist + Geist Mono) and its own accent (ledger blue `#14508c`). Empty four-zone layout
  renders, typecheck/lint/build clean. Detail in `desk/PROGRESS.md`. 4b still blocked on
  Phase 3.
- **2026-09-04 (later)** — TensorMux signed up with Google, API key created and stored in
  `.env` (gitignored, Rohit rotates after). $5/$5 credit verified, expires Sep 18. Only one
  model live: `gemma-4-31b`. Rate limits 15 rpm / 20k tpm. First real call passed and exposed
  two gotchas now written into RESEARCH.md: the model fences its JSON, and it guessed the
  wrong YEAR for a date — both would have poisoned the evidence trail silently.
- **2026-09-05 (S2, `engine`)** — Phase 2 built inside the window: the three-way match, the
  audit trail, the three sources (including the browser), the confidence checklists, the
  refusal, the policy loop and `tieout demo`. 38 tests green, ruff clean. The loop works on
  the real world: one approval from Chris, Controller, and the second short-ship cleared
  itself citing `SHORT-SHIP-01 v1` and his name, with no login and no human.
- **2026-09-06 (S3, `api`)** — Phase 3 built inside the window: eight routes over the engine,
  a background runner and an SSE stream that forwards the engine's own events unchanged, plus
  `python -m tieout.api`. 45 tests green, ruff clean. The four beats were driven end to end
  with nothing but `curl`, and the counters the API returns are the ones the CLI prints.
- **2026-09-05 (S1, `world`)** — Phase 1 built inside the window: seed + ERP + portal + inbox
  + one-command runner + `tieout reset`, 18 tests. The fake company is Kestrel Manufacturing
  Co. buying from 8 suppliers; 40 invoices, 35 clean, 5 broken on purpose. The portal is one
  supplier network with a real form login and a session cookie, so the engine's Phase 2
  sign-in is genuine. Verified with curl and with a real Chromium, not only in tests.
