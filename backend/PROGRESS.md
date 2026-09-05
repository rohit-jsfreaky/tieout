# PROGRESS — backend/

> Working memory for this folder. Read first, update before ending every session.

## Current state — 2026-09-05 (AO session S2, `engine` module)

- **Phase 1 (world) is DONE.** **Phase 2 (engine) is DONE.** Phase 3 (api) not started.
- The Phase 2 finish line passes: `tieout demo` runs all four beats from a fresh reset, and
  `pytest backend/tests -q` is green — **38 tests in ~41 s**, including three that drive a
  real Chromium against the real portal. `ruff check` and `ruff format` clean.
- Verified live, not only in tests: the four beats also run as separate CLI commands against
  a separately running `tieout world`, and the model (`glm-4-7-flash` on TensorMux) really
  does write the fact extractions and the rationale.

## Done

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

### Tests (38 green)

`test_seed.py` (18, Phase 1) · `test_match.py` (5) · `test_evidence.py` (8) ·
`test_policy_loop.py` (3) · `test_refuse.py` (4).

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

## Next action

Phase 3, step 3a in `PLAN.md` (`api/` — thin FastAPI over `engine.investigate.work`, plus
SSE), in AO session S3. `investigate.work()` and the `EventSink` are already the seam the
API needs: `runner.py` runs `work` on a thread and fans `Event` objects out over SSE. Do not
put a rule, a threshold, a Playwright call or a model call in `api/`.

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

## Model notes — new, and NOT yet in RESEARCH.md

`RESEARCH.md` has uncommitted edits in Rohit's main checkout, so this session did not touch
it. **Two findings from this phase are worth adding there by hand:**

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

- None.

## Session log

- **2026-09-03** — folders created, plans written. No code.
- **2026-09-04** — merged into a single backend project.
- **2026-09-05 (S1, `world`)** — Phase 1 built and finished: seed, ERP, portal, inbox, runner,
  CLI, 18 tests. ruff clean. Verified live with curl and a real Chromium sign-in.
- **2026-09-05 (S2, `engine`)** — Phase 2 built and finished: match, evidence, three sources,
  decide, the policy loop, metrics, the CLI and `tieout demo`. 38 tests green, ruff clean.
  The four beats verified twice end to end, once via `tieout demo` and once as separate CLI
  commands against a running world.
