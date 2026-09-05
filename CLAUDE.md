# CLAUDE.md — Tieout (read this first, every session)

**Tieout = an agent that only works the invoices that broke.**

"Tie out" is what accountants say when they make two sets of numbers agree. Tieout ignores the
clean invoices, picks up the exceptions, investigates them across the ERP, the email thread and
the no-API vendor portal, assembles an evidence pack with a proposed decision, escalates once to
a human, and learns the policy from that decision — so the next exception of the same kind
clears itself, citing the rule and the person who approved it.

Built for **Syndicate by Maximor** (hosted by AO). **Track 2: Autonomous Office of the CFO.**
Build window: **Sep 5, 21:30 IST → Sep 7, 03:30 IST (30 hours).** Submit in Discord
`#syndicate-project-showcase` before the end of the window.

## Who is judging, and what they said they want (verified in the Discord, 2026-09-03)

Rayed | Maximor judges. He has **won 22 hackathons**. He will recognise the median project in
three seconds. His own words on what matters:

> "what's most important is **the actual self-improving loop and how the agent is engineered**"
> "demonstrating one domain really well also works"
> internship selection "depends on our project scoring, **presentation** etc" — not on placing

So: the loop is the spine of the demo, the engineering must survive a curious reader, and the
presentation is scored, not decoration. Maximor's own product loop is
`Learns → Runs → Escalates → Improves` and their trademark is **"Audit-Ready Agents"**.
Every decision Tieout makes carries evidence and a human name. That is the pitch they already
believe in.

## What a judge must find in under one minute

1. `backend/src/tieout/engine/policy.py` — the ONLY file that creates, versions and applies rules.
   This IS the self-improving loop. One file.
2. `backend/src/tieout/engine/evidence.py` — the ONLY file that records what the agent found, from
   where, when, with a screenshot. This IS the audit trail. One file.
3. `tieout demo` — one command that runs the four beats end to end from the terminal.

## The evidenced insight (sources in RESEARCH.md)

AP teams spend **60-70% of their time on exceptions**. **45-60 minutes** each. **12.5%** of
invoices need rework. Exceptions add **5-15 days** of payment delay. Everyone automates the
clean 87%. Tieout works the 12.5% that costs the money.

## Folder map (build order = dependency order = AO session order)

**Two things only: a Python backend and a Next.js screen.** No MCP server, no published
package, nothing for anyone to install.

| folder | what | phases | AO sessions | plan |
|---|---|---|---|---|
| `backend/` | ONE Python project, three modules: `world` (fake company, fixture) -> `engine` (the exception loop, the score) -> `api` (thin FastAPI + SSE) | 1, 2, 3 | S1, S2, S3 | `backend/PLAN.md` |
| `desk/` | the one screen. Next.js. The demo. | 4 | S4 | `desk/PLAN.md` |

Root: `MASTER-PLAN.md` (phases + finish lines + hour budget) · `PROGRESS.md` (live state —
read first, update last) · `RESEARCH.md` (verified facts + open questions).

## Working rules (non-negotiable)

1. **Read `PROGRESS.md`** (root + the folder you work in) before anything. Update both before
   ending the session.
2. **Phases in order.** A phase only depends on earlier phases. A phase is DONE only when its
   finish line in `MASTER-PLAN.md` passes.
3. **Code only inside the window.** Sep 5 21:30 IST → Sep 7 03:30 IST. These planning files
   are fine before; code is not. Do not copy code from Cairn (Rohit's other repo) — different
   event, different rules, and Cairn is not finished with its own hackathon. Knowledge
   transfers; code does not.
4. **Use AO for every session.** One AO session per folder, each in its own worktree. The
   judges count AO sessions in the video. Film the Kanban.
5. **Research before building.** Check `RESEARCH.md`. Missing fact → open the real docs with
   Playwright MCP, add it with date + source. Never WebSearch. Never guess.
6. **No fabrication.** Numbers on screen must come from the real run. Sources in the README
   must be real. The judge has seen 22 hackathons' worth of fake demos.
7. **Never run git commit/push, never create repos.** Rohit does all git. He creates the
   public repo himself.
8. **No Anthropic API.** The model is a plain OpenAI-compatible HTTP call behind one file
   (`backend/src/tieout/engine/model.py`), so TensorMux (sponsor, $5 free) and OpenRouter are a
   base-URL swap.
9. **Product-grade.** No temp fixes. If it needs a proper fix, do the proper fix or flag it.
10. **Talk to Rohit in simple English.** Short sentences. No buzzwords.
11. **Cut order when time runs short:** `MASTER-PLAN.md` → "Cut order". Never cut the
    policy-learning beat or the portal beat — those are the demo.

## The four beats (the demo, the tests, and the finish lines all follow this)

1. **Investigate.** A short-shipped invoice. Tieout reads the ERP, reads the email thread,
   **signs into the vendor portal and pulls the delivery note.** Evidence pack appears with a
   proposed decision and a confidence.
2. **Decide once.** The human clicks Approve. A policy is created, **stamped with the
   approver's name and the date.**
3. **Clears itself.** The next short-ship exception is auto-resolved, citing that policy and
   that person. Human touches: 5 → 1.
4. **Refuses.** One exception where nothing lines up. Tieout says "I am not confident. Here is
   what I found. You decide." An agent that knows when to stop, for a judge whose company
   exists because of the trust gap.

## Submission checklist (from the Notion page, verified 2026-09-03)

Post in `#syndicate-project-showcase`:
- [ ] Team name · member names · **Track 2**
- [ ] Public GitHub repo link
- [ ] Live link if deployed (optional)
- [ ] Demo video link — shows the product AND how AO was used (sessions on the Kanban)
- [ ] Brief description · how AO was used during the build

README must state: what it does · how to run it · which track · what agent workflow you
built · **what improved across iterations** (the human-touches counter, before/after) · links.

Also include a short **"Running this for real"** section — the three-tier auth story
(service account / saved session / remote browser handoff for SSO) from `backend/CLAUDE.md`.
A judge who has won 22 hackathons will ask how a portal login works on a headless server.
Most teams will have no answer.

## Canonical lines

- One-liner: **An agent that only works the invoices that broke.**
- The insight: **Everyone automated the invoices that were never the problem. The 12.5% that
  break eat 70% of the team's time.**
- Against the field: **Every other project here automated the easy 87%. This one does the
  12.5% that actually costs the money.**
