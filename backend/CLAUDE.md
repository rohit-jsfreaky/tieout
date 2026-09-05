# CLAUDE.md — backend/ (one Python project, three parts)

Everything server-side lives here: the fake company, the exception loop, and the web API.
**One `pyproject.toml`, one virtualenv, one `pip install -e backend[dev]`.** Three modules
inside, built in order.

Read `PLAN.md` for what to build, `PROGRESS.md` for where we are. Root rules in `../CLAUDE.md`
apply. The only thing outside this folder is `desk/` (the screen), which talks to `api` over
HTTP and never imports Python.

## Stack

Python 3.11+ · FastAPI · uvicorn · sse-starlette · playwright (sync API, own thread) · httpx ·
pydantic v2 · SQLite via stdlib · argparse CLI · pytest · ruff.
**No LLM vendor SDK** — the model is a plain HTTP call (OpenAI-compatible), so TensorMux and
OpenRouter are a base-URL swap.

## Structure

```
backend/
  pyproject.toml            # ONE project. console script: `tieout`
  .env.example              # MODEL_BASE_URL, MODEL_API_KEY, MODEL_ID, PORTAL_USER, PORTAL_PASS
  src/tieout/
    world/                  # PHASE 1 — the fake company (a fixture, not the product)
      seed.py               #   THE data. Deterministic. Every exception is deliberate.
      erp.py                #   :8701 JSON — vendors, purchase_orders, goods_receipts, invoices
      portal.py             #   :8702 HTML — /login (session cookie), /orders, /orders/{po}/delivery-note
      inbox.py              #   :8703 JSON — threads searchable by vendor / po / invoice
      __main__.py           #   `python -m tieout.world` runs all three; `--reset` reseeds
    engine/                 # PHASE 2 — the loop. THE SCORE LIVES HERE.
      models.py             #   Exception, Fact, EvidencePack, Decision, Policy, Metrics
      match.py              #   3-way match. Deterministic. Emits Exceptions with a class.
      sources/erp.py        #   facts from the ERP API
      sources/inbox.py      #   facts from email text (uses model.facts_from_text)
      sources/portal.py     #   THE ONLY PLAYWRIGHT IMPORTER. Signs in, reads the note, screenshots.
      investigate.py        #   runs the three sources for one Exception, stops when enough is known
      evidence.py           #   THE ONLY AUDIT-TRAIL WRITER. source · locator · time · raw · screenshot
      decide.py             #   proposes a Decision + confidence; below the floor -> REFUSE
      policy.py             #   THE ONLY RULE FILE. create · version · match · apply. The loop.
      model.py              #   THE ONLY LLM CALLER. Three named jobs. Base URL + model id pinned.
      metrics.py            #   human touches, auto-cleared, refused, evidence items
      events.py             #   typed events; the library never prints
      store.py              #   SQLite: packs, decisions, policies, metrics
    api/                    # PHASE 3 — thin web layer. NO LOGIC.
      main.py               #   routes
      runner.py             #   one investigation at a time, event fan-out to SSE
      schemas.py            #   request/response models
    cli.py                  # tieout world | match | work | decide | policies | metrics | demo | reset
  tests/
    test_seed.py            # 35 clean matches, 5 exceptions, classed as intended
    test_match.py
    test_policy_loop.py     # THE judge test: approve once -> next same-class auto-clears, citing rule + approver
    test_refuse.py          # E5 refuses; weak evidence never auto-clears
    test_evidence.py        # every Fact has source + time; portal facts have a real screenshot file
```

## Hard boundaries (these ARE the architecture)

1. **`engine/policy.py` owns rules.** Create from a human decision, version when a later
   decision contradicts, match a new Exception, apply. Nothing else touches rules. Every Policy
   carries: id (`SHORT-SHIP-01`), version, condition, action, `approved_by`, `approved_at`,
   `learned_from`, rationale. **This file is the self-improving loop the judge said he scores.**
2. **`engine/evidence.py` owns the audit trail.** A Fact that did not go through it does not
   exist. Every Fact: `source` (erp | inbox | portal), `locator` (URL or query), `observed_at`,
   `raw`, plus `screenshot` for portal facts.
3. **`engine/model.py` is the only LLM caller.** Exactly three named jobs: `facts_from_text`,
   `draft_rationale`, `generalise_decision`. Base URL, key and model id come from env, pinned
   as constants at the top. **Rule application is never an LLM call** — that is what makes
   "auto-cleared citing SHORT-SHIP-01, approved by Chris" reproducible when a judge reruns it.
4. **`engine/sources/portal.py` is the only Playwright importer.** Fresh context per
   investigation. Credentials from env only, never stored in a pack. Screenshot every page read.
   - Playwright is a LIBRARY inside the backend, not a service. It opens a real Chromium on
     this machine, visits our own fake portal, and closes.
   - **HEADED for the demo, headless for tests.** `HEADLESS=0` in `.env` for recording — a
     second browser opening and clicking by itself is the signature shot of the video. A
     hidden browser proves nothing on camera. Default headless so `pytest` stays fast.
   - Playwright's sync API cannot run inside FastAPI's asyncio loop and binds objects to the
     creating thread. Run the browser on its own thread (this cost a debugging round in Cairn).
   - **No Google/SSO login anywhere.** Our portal uses a plain username+password form, which
     is what real B2B vendor/AP portals actually use. Automating a Google button is blocked by
     Google and is not worth fighting.
   - **Sessions persist (BUILD THIS — ~15 min, Playwright does it natively).** After a
     successful login, save the context with `storage_state(path=...)` to
     `~/.tieout/sessions/<vendor>.json`; on the next run load it with
     `new_context(storage_state=...)` and skip the login entirely. This makes the
     "logs in once" claim true and demonstrable instead of hypothetical, and it is the
     honest foundation of the production story below.

   **The production auth story — README section, and the answer to the obvious judge
   question "how does this work on a server with no screen?" (Rohit raised it 2026-09-04).**
   Three tiers, only tier 2 gets built this weekend:
   1. **Service account.** IT provisions `tieout-bot@company.com` with its own credentials,
      usually SSO-exempt and read-only. This is what enterprises actually do; RPA tools have
      worked this way in finance for 15 years. Most deployments never need a human login.
   2. **Session persistence.** Log in once, reuse the saved session for weeks. ← WE BUILD THIS
   3. **Remote browser handoff, for SSO/2FA.** The browser runs on the server; its screen is
      streamed into the user's own tab (VNC in an iframe, or Chrome's screencast protocol —
      hosted browser providers sell this as a feature). The user clicks a link, sees the real
      remote browser, signs in, does 2FA on their phone. The cookie is created on the server
      where the agent needs it. Same experience as a bank's "connect your account" flow.
      DO NOT BUILD — that is a week, not a weekend.
5. **Refusing is a first-class outcome**, not an error. The confidence floor is a named constant.
6. **`api/` holds no logic.** If you are about to write a rule, a threshold, a Playwright call
   or an LLM call there — stop, it belongs in `engine/`.
7. **Human touches are computed from the store**, never hard-coded. One Approve = one touch,
   an auto-clear = zero.
8. Events out, never prints. The CLI renders them; the API streams them.

## Clean code rules

- Type hints everywhere; `ruff check` + `ruff format` clean before ending a session.
- Small functions. Pydantic models across every file boundary. No loose dicts.
- No bare `except:`. No magic numbers — tolerances and thresholds are named constants.
- Secrets from env only. `.env` git-ignored, `.env.example` committed.
- The five tests listed above are not optional.

## Definition of done for any task here

Code + ruff clean + tests green + PROGRESS.md updated. All four.
