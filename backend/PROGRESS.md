# PROGRESS — backend/

> Working memory for this folder. Read first, update before ending every session.

## Current state — 2026-09-05 (AO session S1, `world` module)

- **Phase 1 is DONE.** The finish line in `../MASTER-PLAN.md` passes end to end (evidence
  below). Phases 2 and 3 not started.
- One Python project installs and runs: `pip install -e backend[dev]` from the repo root,
  console script `tieout`.
- Verified live, not just in tests: three servers up from one command, `curl` returns 40
  invoices, a real Chromium signed into the portal and read "95" off delivery note DN-1042,
  reset put a deleted invoice back.

## Done

### Phase 1 — `world/` (steps 1a–1d)

- `backend/pyproject.toml` — one project, `tieout` console script, ruff + pytest config.
- `world/seed.py` — the whole fake company in one file: pydantic shapes, the data, the
  SQLite schema, seed/reset, and the query functions the three servers use.
  - Kestrel Manufacturing Co., USD, 8 suppliers, dates anchored to the current month.
  - 40 invoices: 35 tie out; 5 are broken on purpose, exactly per `PLAN.md`.
  - `SEED_EXCEPTIONS` documents the five for tests and README. **The engine never reads it**
    — Phase 2 has to find them with a real three-way match.
- `world/erp.py` — :8701 JSON. Four tables, list + get, filters by vendor / po / invoice /
  status. Every list answers `{count, items}`.
- `world/portal.py` — :8702 VendorLink, HTML only, no API. Real login (form post, session
  cookie, 303 back to `/login?next=…` when signed out), `/orders`, `/orders/{po}/delivery-note`.
  The two on-camera pages are styled.
- `world/inbox.py` — :8703. `GET /threads?vendor=&po=&invoice=&q=`, plus `/threads/{id}`.
- `world/__main__.py` — `python -m tieout.world` runs all three on their own threads;
  `--fresh` reseeds then serves; `--reset` reseeds and exits.
- `cli.py` — `tieout world` and `tieout reset` (Phase 2 adds the engine commands here).
- `tests/test_seed.py` + `tests/conftest.py` — 18 tests, all green. Temp database, pinned
  month, so tests never touch `~/.tieout`.

### The five seeded exceptions

| ref | invoice | po | class | what is wrong |
|---|---|---|---|---|
| E1 | INV-3036 | PO-1042 | short_ship | billed 100 boxes, receipt 95; portal note + email say 95 |
| E2 | INV-3037 | PO-1043 | short_ship | billed 60, receipt 58 (same supplier as E1 — the policy clears this one) |
| E3 | INV-3038 | PO-1044 | price_variance | 52.00 invoiced vs 50.00 on the PO = 4%; email explains the surcharge |
| E4 | INV-3039 | PO-1045 | missing_po | no PO number; exactly one open PO fits (same vendor, amount, week) |
| E5 | INV-3040 | — | unknown | no PO, no receipt, no email, not on the supplier network → REFUSE |

## How to run it

```bash
pip install -e backend[dev]        # from the repo root
tieout world                       # or: python -m tieout.world
tieout reset                       # world back to the seed
pytest backend/tests -q
curl http://127.0.0.1:8701/invoices
curl 'http://127.0.0.1:8703/threads?po=PO-1042'
# browser: http://127.0.0.1:8702/orders/PO-1042/delivery-note
# sign in as ap-bot@kestrelmfg.com / tieout-demo
```

## Next action

Phase 2, step 2a in `PLAN.md` (`engine/` — models, store, three-way match), in AO session S2.
`tieout match` must find exactly these five and class them correctly, **without** reading
`SEED_EXCEPTIONS`.

## Decisions made

- One Python project, three modules (`world`, `engine`, `api`). Not three packages.
- Rule application is deterministic code, never an LLM call. Reproducibility is the point.
- Refusing is a first-class outcome with its own demo beat.
- `policy.py` and `evidence.py` are single-owner files, so a judge finds the loop and the
  audit trail in under a minute.
- LLM access is a plain OpenAI-compatible HTTP call. TensorMux and OpenRouter differ only by
  base URL, so switching providers mid-build costs nothing.
- **The portal is one supplier network ("VendorLink") with one buyer account**, not eight
  vendor sites. One real login to automate, which is what the session-persistence story in
  `CLAUDE.md` needs. Ardent Systems (E5) is not on the network, so the portal genuinely has
  nothing on it.
- **The world is SQLite at `~/.tieout/world.db`**, rebuilt from the seed on reset. Row per
  document with the pydantic JSON in a `doc` column plus the columns worth filtering on.
- **Dates follow the current month** so the demo never looks stale; `TIEOUT_SEED_MONTH` pins
  them for tests. Amounts go through one `money()` helper (Decimal, half-up).
- Portal credentials come from env (`PORTAL_USER` / `PORTAL_PASS`) with the demo world's own
  values as the fallback, so no password is ever written into a stored artefact.

## Blockers

- None. Model base URL / key / id are decided and tested (`../RESEARCH.md`) but not yet used;
  Phase 2's `model.py` is the first thing that will call them.

## Session log

- **2026-09-03** — folders created, plans written. No code.
- **2026-09-04** — merged into a single backend project.
- **2026-09-05 (S1, `world`)** — Phase 1 built and finished: seed, ERP, portal, inbox, runner,
  CLI, 18 tests. ruff clean. Verified live with curl and a real Chromium sign-in.
