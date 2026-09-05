# MASTER-PLAN — Tieout

One page. Phases, order, finish lines, hour budget. Details live in `backend/PLAN.md` and `desk/PLAN.md`.

**Rule:** a phase only depends on earlier phases. A phase is DONE only when its finish line
passes. No half-done phases.

## The shape of the product

An **exception desk** for accounts payable. Not an invoice processor. It never touches a clean
invoice. It runs the 3-way match (PO vs goods receipt vs invoice), takes only the mismatches,
and for each one: investigates across three sources (ERP, inbox, **vendor portal with no API**),
assembles an evidence pack, proposes a decision with a confidence, escalates once to a human,
and **learns a policy from the human's decision** so the same class of exception never needs a
human again. Every fact and every decision is on the audit trail with a source, a time, and a
name.

The LLM (OpenRouter only) does exactly three things: turns unstructured text (emails, delivery
notes) into facts, drafts the rationale for a proposed decision, and generalises a human
decision into a candidate rule. **Matching, evidence collection, rule application and the
confidence gate are deterministic code.** That is what makes "auto-cleared, citing rule
SHORT-SHIP-01 approved by Chris" reproducible and trustworthy — and it is the engineering the
judge said he scores.

Build order follows dependencies: world → engine → api → desk.

## Hour budget (30 h window, plan for ~24 working hours)

| phase | folder | hours | window (IST, suggested — Rohit owns the clock) |
|---|---|---|---|
| 0 setup | — | before the 5th | done before 21:30 Sat |
| 1 world | `backend/` (world) | 3 | Sat 21:30 → Sun 00:30 |
| 2 engine | `backend/` (engine) | 9 | Sun 00:30 → 02:00, sleep, Sun 08:00 → 15:30 |
| 3 api | `backend/` (api) | 2 | Sun 15:30 → 17:30 |
| 4 desk | `desk/` | 6 | Sun 17:30 → 23:30 |
| 5 harden + ship | root | 3 + buffer | Sun 23:30 → Mon 02:30, submit by 02:30, hard stop 03:30 |

Phase 1 is time-boxed. If world is not done at 3 hours, ship what exists and move on — it is a
fixture, not the product.

---

## Phase 0 — Setup · before Sep 5

- AO installed (Windows build), one practice session completed on a throwaway repo. Learn:
  add project → new session → worktree → follow-up message → review. Do NOT learn AO at hour 1.
- OpenRouter key funded; model chosen and recorded in `RESEARCH.md`; one test call works.
- Playwright + Chromium installed. Node + Python envs ready.
- 30 minutes of finance reading: 3-way match, short-ship, price variance, non-PO invoice.
  Notes in `RESEARCH.md`.
- Rohit creates the empty public GitHub repo (MIT).

**FINISH LINE:** an AO session has been opened, worked in, and closed on a throwaway repo, and
one OpenRouter call returns text.

## Phase 1 — World · `backend/` module `world` · 3 h

The fake company. ERP (SQLite + FastAPI), vendor portal (login + delivery notes), inbox (JSON).
Seed: 40 invoices, 5 exceptions across 3 classes, plus 1 deliberately unresolvable.

**FINISH LINE:** one command starts all three; `curl` lists invoices from the ERP; a browser
can sign into the portal and open a delivery note; the inbox has the vendor threads. Reset
command returns everything to the seed.

## Phase 2 — Engine · `backend/` module `engine` · 9 h

The loop. This is the score.

**FINISH LINE — the four beats from the CLI:**
1. `tieout match` → exactly the 5 seeded exceptions, classed correctly.
2. `tieout work <id>` on the short-ship → evidence pack with ERP facts + the email + **the
   portal delivery note fetched by Playwright with a screenshot**, a proposed decision and a
   confidence.
3. `tieout decide <id> approve --by "Chris, Controller"` → policy created with name + date;
   `tieout work <id2>` on the second short-ship → **auto-cleared, citing the policy and Chris**.
4. `tieout work <id5>` on the unresolvable one → **refused** with what it found.
`pytest` proves 1-4 without a human. `tieout demo` runs all four beats in sequence.

## Phase 3 — API · `backend/` module `api` · 2 h

Thin FastAPI over the engine. Queue, evidence pack, decide, policies, metrics, reset, and an
SSE stream of investigation steps and evidence as they happen.

**FINISH LINE:** the four beats via `curl` alone, with the SSE stream showing the portal login
step live.

## Phase 4 — Desk · `desk/` · 6 h

The one screen. Queue left, evidence pack + decision centre, policies + counters right.

**FINISH LINE:** the four beats driven from the screen with no terminal on camera, and the
60-second stranger test: someone with zero context watches beats 2-3 and can say "it learned
from the approval, that is why the second one cleared itself".

## Phase 5 — Harden + ship · root · 3 h + buffer

- Run `tieout demo` and the screen flow 5× from a fresh reset. Fix whatever moves.
- Record the video: the four beats + a cut to the AO Kanban with the sessions.
- README per the checklist in `CLAUDE.md`. Numbers in it come from the real run.
- Post in `#syndicate-project-showcase`. Submit early — the window closes at 03:30 IST Monday.

**FINISH LINE:** the Discord post is up with all fields, and the repo + video open in a
private browser window.

---

## Cut order when time runs short

1. Desk polish beyond the three panels (animations, empty states)
2. The refuse beat's UI (keep it in the CLI + README)
3. The SSE stream (fall back to polling; the screen still works)
4. Seeded exception classes 3 → 2 (keep short-ship and one more)
5. NEVER: the portal beat, the policy-learning beat, the approver stamp, the video, the README.

## AO session plan (this is what the judges will look at)

| session | works on | branch | what it produces |
|---|---|---|---|
| S1 | `backend/src/tieout/world/` | `world` | fixtures + seed + run/reset commands |
| S2 | `backend/src/tieout/engine/` | `engine` | the loop + tests + `tieout demo` |
| S3 | `backend/src/tieout/api/` | `api` | routes + SSE |
| S4 | `desk/` | `desk` | the screen |
| S5 | root | `ship` | README, hardening fixes, video assets |

Different modules, so two sessions rarely touch the same file even though they share one
Python project.

One worktree each. Merge in order. Use AO's follow-up messages and review runs — those are
the features that show up on the Kanban. Screenshot the Kanban at least three times during
the build for the video.
