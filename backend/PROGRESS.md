# PROGRESS — backend/

> Working memory for this folder. Read first, update before ending every session.

## Current state — 2026-09-06 (AO session S5, harden + ship)

- **Nothing is being built here any more.** S5 hardened what exists and wrote the root
  `README.md`. `pytest backend/tests -q` is **46 green**, `ruff check` and `ruff format` clean.
- **`tieout reset` + `tieout demo` was run five times from cold.** Runs 2–5 were
  byte-identical; run 1 differed only in the E1 rationale paragraph, which is model prose.
  Every reproducible thing was identical in all five. ~22 s a run.
- **Two changes to the engine, both from Rohit:**
  - **`RATIONALE_SYSTEM` in `model.py` was inverting the finding.** On E4 it wrote "Exception
    E4 is invalid because the supplier confirmed there is no order number" — backwards. The
    prompt now states that the exception is an established finding raised by a deterministic
    three-way match, forbids valid/invalid/unfounded/false-positive, and fixes the order of
    the paragraph; the user message now opens "Confirmed exception E4 ... / What did not tie
    out". Verified over three consecutive E4 runs: "Invoice INV-3039 ... did not tie out
    because it lacked an order number". Fixed in the prompt, not filtered afterwards.
  - **`Metrics.open_not_worked`** — the exceptions nobody has picked up yet. `worked` and
    `open_not_worked` always add up to `exceptions_found`, so the counters can no longer show
    5 found and 3 worked and quietly lose the other 2. It is in `metrics.compute`, in
    `_print_metrics` ("Open, not yet worked"), and asserted in `test_api.py` and
    `test_policy_loop.py`. Note the contract it exposes: straight after `POST /reset` the
    store is empty, so **every counter is 0 until something runs the match** (`GET /queue` or
    `tieout match`). That is honest — Tieout has found nothing because it has not looked — but
    it is a real ordering requirement for any client, and it caught the desk out.
- **`tieout work E3` and `tieout work E4` after a reset**: both propose at 100% confidence
  (`approve`, and `attach_po`). Neither needs the browser — their checklists are satisfied
  after the inbox.
- **The no-key path was verified** (`tieout demo` with `MODEL_API_KEY` empty). Identical: the
  counters that matter, and the rule's id, version, condition, action, approver, `learned_from`
  and citation. Different: the rule's human-readable name and rationale (code prose), and
  `evidence_items` — **12 instead of 16**, because the model splits a vendor email into up to
  three claims where the code records it verbatim as one.

## Earlier — 2026-09-06 (AO session S3, `api` module)

- **Phase 1 (world), Phase 2 (engine) and Phase 3 (api) are all DONE.**
- The Phase 3 finish line passes: **the four beats run through `curl` alone**, with the SSE
  stream showing the VendorLink sign-in live. Verified against a real `python -m tieout.api`
  on :8700 with a real Chromium — not only in tests.
- `pytest backend/tests -q` is green — **46 tests in ~60 s**, including six that drive a real
  Chromium against the real portal. `ruff check` and `ruff format` clean.
- The Phase 2 finish line still passes: `tieout demo` runs all four beats from a fresh reset,
  and the model (`glm-4-7-flash` on TensorMux) really does write the fact extractions and the
  rationale.

## Done

### Phase 3 — `api/` (steps 3a–3c)

**Nine routes, and not one line of product logic.** `main.py` only asks the engine, reads
the store and returns the pydantic object.

```
GET  /queue                    three-way match, then the five exceptions + where each got to
GET  /exceptions/{id}          the evidence pack, the decision, and the rule it cited
POST /exceptions/{id}/work     202; runs on a thread. ?portal=false skips the browser
GET  /exceptions/{id}/events   SSE: the engine's own Event objects, verbatim
POST /exceptions/{id}/decide   {action, by, note?} -> the decision AND the rule it learned
GET  /policies                 every rule, every version, with cited_by
GET  /metrics                  the counters, computed from the store on every request
POST /reset                    world + store + saved session + screenshots back to zero
GET  /screenshots/{name}       the PNG a portal Fact points at (added for the desk, 4b)
```

- **`runner.py`** starts `engine.investigate.work` on a worker thread and fans the engine's
  `Event` objects out to every open stream **unchanged**. It buffers them too, so
  `POST /work` followed by `GET /events` cannot lose the first few — the replay and the
  subscription are taken under one lock, so a stream never misses an event or sees one twice.
- **The stream also carries the decide beat.** `POST /decide` passes the same sink, so
  `decided` and `policy_learned` land on that exception's stream as well.
- **One investigation at a time** (409 otherwise): the browser, the saved VendorLink session
  and the screenshot folder are a single shared resource. `POST /reset` during a run is also
  a 409 rather than a silent loss.
- **The API starts the world itself** if the ERP is not answering, and stops only what it
  started — so `python -m tieout.api` plus `curl` is the whole demo.
- The only shape on the wire the engine did not write is the stream's own `done` message
  (`{exception_id, state, error}`), which is transport, not evidence.

### Phase 2 — `engine/` (steps 2a–2e)

**2a. Models, store, match**
- `models.py` — every shape: `ExceptionCase`, `Fact`, `LookupStep`, `Check`, `Decision`,
  `EvidencePack`, `PolicyCondition`, `Policy`, `Metrics`. Derived numbers (`short_pct`,
  `price_variance_pct`, `exposure`, `supported_amount`) are pydantic computed fields, so the
  API and the desk get them for free.
- `match.py` — the real three-way match over the ERP's JSON API. Finds exactly the five
  seeded exceptions and classes them `short_ship` / `price_variance` / `missing_po` /
  `unknown`. Ids `E1..E5` are assigned in invoice order by the matcher itself.
- `store.py` — SQLite at `~/.tieout/engine.db`: exceptions, packs, decisions, policies.
  Separate from the world's database: the world is the company's data, this is the agent's
  own memory. Every policy version is kept.

**2b. Evidence and the three sources**
- `evidence.py` — the only audit-trail writer. Refuses a portal fact with no screenshot on
  disk, a fact dated outside the open period, and a fact with no locator or raw material.
- `sources/erp.py` — its own DTOs parsed from the ERP's JSON (the engine never imports the
  world). Records the invoice, the order, the receipt, or the single candidate order.
- `sources/inbox.py` — searches by order, then invoice, then supplier, and turns the vendor's
  own words into facts via `model.facts_from_text`.
- `sources/portal.py` — the only Playwright importer. Signs in, reads the delivery note off
  the rendered page, screenshots it, and **saves the session with `storage_state`** so the
  next investigation walks straight in. It deliberately does not sign out.
- `investigate.py` — ERP -> inbox -> portal, stopping the moment the class's checklist is
  satisfied. `work()` is the whole beat and is shared with Phase 3 so `api/` holds no logic.

**2c. Decide and refuse**
- `decide.py` — a written checklist per class; the confidence is the weight that passed.
  `CONFIDENCE_FLOOR = 0.70`, plus a named **required check** per class that must pass
  whatever the score says. Below either, the outcome is a refusal that lists where it looked.

**2d. The policy loop**
- `policy.py` — `learn` / `match` / `apply`. The model drafts a name and suggests a
  tolerance; **the code clamps it** (never narrower than the case it was learned from, never
  wider than the class ceiling) and pins the rule to that supplier. A rejection of something
  a rule would have cleared narrows the rule into a **new version**; the old version is kept
  and marked superseded.

**2e. Metrics, CLI, demo**
- `metrics.py` counts everything from the store. `cli.py` has `world`, `match`, `work`,
  `decide`, `policies`, `metrics`, `demo`, `reset`, and is the only thing that prints.
- `world/__main__.py` gained `start_background()` so `tieout demo` can run the company
  in-process for the length of the demo. `serve()` now uses it.

### Tests (46 green)

`test_seed.py` (18, Phase 1) · `test_match.py` (5) · `test_evidence.py` (8) ·
`test_policy_loop.py` (3) · `test_refuse.py` (4) · `test_api.py` (8, Phase 3).

- `test_api.py` drives the real app over real HTTP against the real test world, subscribing
  to the stream **before** starting the work, exactly as the desk will. It asserts the
  VendorLink sign-in step arrives live, that every SSE message has precisely the fields of
  `engine.events.Event` (so a reshape here breaks a test rather than the desk), that one
  approval makes E2 auto-clear citing the rule and Chris, that E5 refuses, and that a second
  `/work` while one is running is a 409.

- `test_match.py::test_the_engine_cannot_read_the_seed` scans every engine file for
  `SEED_EXCEPTIONS` or an import of the world. The architectural promise is enforced, not
  just documented.
- `test_policy_loop.py` is the judge test: approve E1 once -> `SHORT-SHIP-01 v1` stamped with
  Chris, Controller -> E2 auto-clears citing rule and approver -> a different class does not
  match -> a contradicting decision produces v2 and keeps v1.
- Tests run **offline**: `conftest.py` empties `MODEL_API_KEY`, so the engine falls back to
  the prose it writes itself and every reproducible part is unaffected.

## What the demo prints (2026-09-05, real run)

5 exceptions found · 3 worked · **1 human touch** · 1 auto-cleared citing `SHORT-SHIP-01 v1`
approved by Chris, Controller · 1 refused · 16 evidence items · 3 screenshots · 1 active
policy · 1 citation. Working all five gives 5 worked / 28 evidence items.

`GET /metrics` after the same four beats over curl (2026-09-06) returns exactly those
numbers — the API counts nothing of its own.

## How to run it

```bash
pip install -e backend[dev]        # from the repo root
tieout demo                        # the four beats, from a cold start (~90 s)
tieout world                       # or run the company yourself, then:
tieout match
tieout work E1
tieout decide E1 approve --by "Chris, Controller"
tieout work E2                     # auto-cleared, citing the rule and Chris
tieout work E5                     # refused
tieout policies ; tieout metrics
pytest backend/tests -q
HEADLESS=0 tieout demo             # a real browser window, for the video
```

### The four beats over curl (the Phase 3 finish line)

```bash
python -m tieout.api               # :8700, and starts the company if it is not running
curl -X POST :8700/reset
curl :8700/queue                                     # the five exceptions

curl -N :8700/exceptions/E1/events &                 # beat 1: watch it happen
curl -X POST :8700/exceptions/E1/work                #   ... the VendorLink sign-in is live

curl -X POST :8700/exceptions/E1/decide \            # beat 2: the rule is born
  -H 'Content-Type: application/json' \
  -d '{"action":"approve","by":"Chris, Controller"}'

curl -N :8700/exceptions/E2/events &                 # beat 3: auto_cleared,
curl -X POST :8700/exceptions/E2/work                #   citing SHORT-SHIP-01 v1 and Chris

curl -N :8700/exceptions/E5/events &                 # beat 4: refused
curl -X POST :8700/exceptions/E5/work

curl :8700/policies ; curl :8700/metrics
```

## Next action

Nothing here. Phase 4 (`desk/`) is done too — see `desk/PROGRESS.md`.

**The ninth route exists now (added 2026-09-06 by S4).** Phase 3 deliberately stopped at
eight, which left the desk unable to show a screenshot: a `Fact.screenshot` is an absolute
path on this machine (`~/.tieout/screenshots/E1-PO-1042.png`) and a browser cannot open one.
`GET /screenshots/{name}` is a `FileResponse` over `engine.sources.portal.screenshot_dir()`
and holds no logic: the name is reduced to its last component and must resolve directly
inside that folder, so nothing else on disk is reachable.
`test_the_screenshot_a_fact_points_at_is_served_as_bytes` covers the happy path and four
escape attempts. It is what the desk's live browser panel draws.

## Decisions made (Phase 2)

- **The exception model is `ExceptionCase`, not `Exception`.** Shadowing the builtin in a
  module every other file imports is not worth the tidier name.
- **The engine never imports the world.** `sources/erp.py` and `sources/inbox.py` parse the
  APIs into their own DTOs, exactly as they would against NetSuite or a real mailbox. A test
  enforces it.
- **The checklist is the confidence.** Weighted pass/fail per class, so a judge can predict
  the number from the evidence. No model produces a confidence anywhere.
- **Two ways to refuse:** below the floor, or a failed *required* check. The second one stops
  a high-scoring pack from approving something whose one essential fact is missing.
- **The model proposes, the code disposes.** `generalise_decision` may suggest a tolerance
  and a scope; `policy.py` clamps the tolerance and always pins the rule to the supplier,
  noting on the rule when it narrowed the draft.
- **A rule never rescues a thin pack**: `policy.covers()` also requires the class's required
  check to pass, which is why E2 with the portal switched off refuses instead of clearing.
- **The portal source does not sign out** — persisting the session is the point.
- **`tieout reset` wipes the world, the engine store, the saved session and the screenshots**,
  so every demo starts genuinely cold.

## Decisions made (Phase 3)

- **The stream carries `engine.events.Event` verbatim.** No envelope, no renaming, no derived
  fields. The SSE event name is the event's own `kind`, and a test asserts the field set, so
  the desk can type straight against the engine's model.
- **The API adds exactly one shape of its own: `done`.** SSE has no other way to say "this
  run is over", and it carries transport state (`state`, `error`), never evidence.
- **Events are buffered per exception, so a late subscriber loses nothing.** The desk can
  `POST /work` and then subscribe, or subscribe first — both give the same complete stream.
  Replay and subscription happen under one lock.
- **One investigation at a time, enforced with a 409.** A second browser against the same
  saved session and the same screenshot folder is a race, not a feature.
- **The API starts the world if nobody else has, and stops only what it started.** Otherwise
  the "four beats over curl" claim quietly depends on a second terminal.
- **`?portal=false` on `/work`** mirrors the CLI's `--no-portal`, so the API is testable
  without Chromium. It is a transport knob, not a rule.
- **No `/health` route.** `PLAN.md` lists eight; eight is what exists.

## Model notes — now IN RESEARCH.md (moved there by S5, 2026-09-06)

These two are gotchas 3 and 4 under "Model provider" in `RESEARCH.md`, along with a fifth one
S5 found (the model inverting a finding in the rationale). Kept here for the record:

1. **`chat_template_kwargs: {"enable_thinking": false}` turns the reasoning off** on
   TensorMux's `glm-4-7-flash`, and this is the single biggest reliability win of the phase.
   Measured 2026-09-05 on the same prompt: **2.9 s and 150 completion tokens with it, against
   19.7 s and 1,912 without** — and at `max_tokens=800` without it, `content` came back
   **empty** because the whole budget went into `reasoning`. `engine/model.py` sends it on
   every call. A provider that does not understand the field ignores it, which is why (2)
   still exists.
2. **Empty content is retried with more room, not more patience.** `MODEL_MAX_TOKENS` (800)
   is the starting budget; on a reasoning-only reply the retry doubles it (800 -> 1600 ->
   3200) with no sleep. HTTP 429/5xx keep the ordinary backoff. Floor of 600 enforced.

Both gotchas already in RESEARCH.md were confirmed live and are handled: the model fences its
JSON (stripped in `_strip_fence`), and it invents the year unless told today's date (every
prompt carries `_dateline`, and `evidence.py` rejects an out-of-window date — there is a test
that feeds it 2024 and expects a rejection).

## Blockers

- None. The ninth route (`GET /screenshots/{name}`) was added on 2026-09-06 — see
  "Next action".
- Note for anyone working in an AO worktree: `pip install -e backend[dev]` is bound to
  whichever worktree ran it, so `pytest` can silently test another session's code. Run
  `PYTHONPATH=<this worktree>/backend/src python -m pytest backend/tests -q` to be sure.

## Session log

- **2026-09-06 (S5, harden + ship)** — five cold demo runs, `work E3`/`work E4`, the no-key
  path. Fixed the rationale prompt and added `open_not_worked`. 46 tests green, ruff clean.
- **2026-09-03** — folders created, plans written. No code.
- **2026-09-04** — merged into a single backend project.
- **2026-09-05 (S1, `world`)** — Phase 1 built and finished: seed, ERP, portal, inbox, runner,
  CLI, 18 tests. ruff clean. Verified live with curl and a real Chromium sign-in.
- **2026-09-05 (S2, `engine`)** — Phase 2 built and finished: match, evidence, three sources,
  decide, the policy loop, metrics, the CLI and `tieout demo`. 38 tests green, ruff clean.
  The four beats verified twice end to end, once via `tieout demo` and once as separate CLI
  commands against a running world.
- **2026-09-06 (S3, `api`)** — Phase 3 built and finished: eight routes, the background
  runner and the SSE fan-out, plus `python -m tieout.api`. 45 tests green, ruff clean. The
  four beats verified through `curl` alone against a live server: the stream showed the
  VendorLink sign-in on E1, E2 reused the saved session and auto-cleared citing
  `SHORT-SHIP-01 v1` and Chris, Controller, and E5 refused listing the eight places it
  looked. `GET /metrics` returned the same numbers the CLI prints.
