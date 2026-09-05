# PLAN — backend/ (Phases 1-3, ~14 hours)

Finish lines in `../MASTER-PLAN.md`. Steps in order; each only depends on the ones above it.

---

# PHASE 1 — `world/` · 3 hours · TIME-BOXED

A fixture, not the product. If the clock hits 3 h, ship what exists and move to the engine.

**Why it exists:** real finance data is impossible to get in 30 hours, and every other team
will demo on a CSV. This world has a **vendor portal with no API** — the thing the engine signs
into with a browser, on camera. That is the signature shot.

### The seed (the demo script in data form — do not improvise it)

40 invoices, ~8 vendors. 35 match cleanly. 5 do not:

| id | class | what is wrong | where the truth lives | intended outcome |
|---|---|---|---|---|
| E1 | short-ship | invoice 100 units, receipt 95 | portal delivery note says 95; email "shipped 95, rest next week" | short-pay for 95 -> human approves -> POLICY BORN |
| E2 | short-ship | invoice 60, receipt 58 | portal delivery note says 58; email confirms | **auto-cleared by E1's policy** |
| E3 | price variance | unit price 52 vs PO 50 (4%) | email: freight surcharge notice | approve within tolerance -> optional 2nd policy |
| E4 | missing PO | invoice has no PO number | ERP has one open PO: same vendor, amount, week | attach PO, approve |
| E5 | unresolvable | vendor has no PO, no receipt, no email, nothing in the portal | **REFUSE** — "not confident, here is what I found" |

Vendor names must read as real. Pick one currency and keep it.

### 1a. Seed + ERP (60 min)
- `world/seed.py` — deterministic ids, dates in the current month, the 5 exceptions exactly as
  above. `world/erp.py` — :8701 JSON, list/get for the four tables, filter by vendor/po/invoice.
- ✅ `curl :8701/invoices` returns 40; filters work.

### 1b. Vendor portal (75 min) — the on-camera piece
- :8702. `/login` (form, session cookie, redirect when signed out), `/orders`,
  `/orders/{po}/delivery-note` (PO, ship date, line items with shipped qty, a note field —
  E1 and E2 carry the short-ship note here).
- A **real** login: session cookie and a redirect, so the engine's sign-in is genuine, not a
  bypass. Two pages get visual care because they are on camera. Nothing else does.
- ✅ sign in by hand in a browser, open E1's delivery note, see "95".

### 1c. Inbox (30 min)
- :8703. `GET /threads?vendor=&po=&invoice=&q=`. E1/E2/E3 have the relevant vendor emails.
  **E5 deliberately has none.**
- ✅ `curl ':8703/threads?po=PO-1042'` returns the short-ship thread.

### 1d. Run + reset + test (15 min)
- `python -m tieout.world` starts all three; `--reset` reseeds. `tests/test_seed.py`.
- ✅ **Phase 1 finish line.**

---

# PHASE 2 — `engine/` · 9 hours · THE SCORE

### 2a. Models + store + match (75 min)
- Pull POs, receipts, invoices from the ERP; 3-way match; emit Exceptions with a class
  (`short_ship` | `price_variance` | `missing_po` | `unknown`).
- ✅ `tieout match` prints exactly the 5 seeded exceptions, correctly classed. Test.

### 2b. Evidence + the three sources (150 min)
- `evidence.py` FIRST — the Fact shape and the trail writer.
- `sources/erp.py` — PO, receipt, invoice facts.
- `sources/inbox.py` — search threads; `model.facts_from_text` turns email bodies into Facts
  ("vendor states 95 units shipped on Sep 2").
- `sources/portal.py` — Playwright: sign in from env creds, open the PO's delivery note, read
  shipped quantities and the note, screenshot, sign out. Own thread.
  **Session persistence (15 min, do not skip):** after login, `storage_state(path=...)` to
  `~/.tieout/sessions/<vendor>.json`; next run loads it and skips the login. Prove it in the
  demo — the second investigation on the same vendor never sees a login page. This is what
  makes the production auth story in `CLAUDE.md` real rather than a claim.
- `investigate.py` — erp -> inbox -> portal, stop when the class's required facts are present.
- ✅ `tieout work E1` shows a pack with ERP facts, the email fact, and the portal fact with a
  screenshot path. Test asserts source + time on every Fact and that the screenshot file exists.

### 2c. Decide + refuse (60 min)
- Per class, a deterministic checklist of required facts -> confidence.
  `model.draft_rationale` writes the one-paragraph "why". Below `CONFIDENCE_FLOOR` -> REFUSE.
- ✅ E1 proposes "short-pay for 95 units" with high confidence. E5 refuses, listing where it
  looked. Test.

### 2d. The policy loop (120 min) — THE JUDGE TEST
- `policy.py`: `learn(decision) -> Policy` (`model.generalise_decision` drafts it, then it is
  stored as a **deterministic condition the code evaluates** — vendor, class, tolerance),
  `match(exception) -> Policy | None`, `apply(policy, exception) -> Decision(auto=True,
  cited_policy=..., approved_by=...)`.
- `tieout decide E1 approve --by "Chris, Controller"` -> `SHORT-SHIP-01 v1`.
- `tieout work E2` -> matched -> **auto-cleared, citing SHORT-SHIP-01 and Chris**.
- A later contradicting decision -> `v2`, v1 kept for the audit.
- ✅ `test_policy_loop.py`: approve once, next same-class exception clears itself with the
  citation; a different class does NOT match; a contradiction versions the rule.

### 2e. Metrics + CLI + demo (75 min)
- `metrics.py` from the store. `cli.py` complete: `world`, `match`, `work`, `decide`,
  `policies`, `metrics`, `reset`, and **`demo`** = the four beats in sequence with the counters
  printed at the end.
- ✅ **Phase 2 finish line:** `tieout demo` from a fresh reset runs all four beats; `pytest` green.

### 2f. Optional, only if 2a-2e fit inside 9 h
- E3's price-variance policy with a `<= 5%` tolerance — a second learned rule for the README.
- A Neatlogs trace of one investigation.

---

# PHASE 3 — `api/` · 2 hours

```
GET  /queue                        exceptions: class, status, confidence
GET  /exceptions/{id}              evidence pack + proposed decision (or refusal)
POST /exceptions/{id}/work         start investigation (background)
GET  /exceptions/{id}/events       SSE: steps and Facts as they land, then the decision
POST /exceptions/{id}/decide       {action, by, note?} -> returns the new/updated Policy
GET  /policies                     active rules: version, approver, learned_from, cited_by
GET  /metrics                      human touches, auto-cleared, refused, evidence items
POST /reset                        world + engine store back to the seed
```

### 3a. Skeleton (30 min) — app, schemas, CORS, `/reset`, `/queue`, `/metrics`, `/policies`.
✅ `curl :8700/queue` lists the 5 exceptions after a reset.

### 3b. Work + stream (60 min) — `runner.py` runs `investigate` in a background thread, fans
engine events out over SSE. ✅ `curl -N :8700/exceptions/E1/events` shows the portal sign-in
step and each Fact live.

### 3c. Decide (30 min) — returns the Policy so the desk shows the stamp instantly.
✅ **Phase 3 finish line:** the four beats via curl alone.

### Deliberately NOT building
Auth, users, history pages, deployment config. Localhost demo.
