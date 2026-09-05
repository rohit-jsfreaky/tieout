# Tieout

**An agent that only works the invoices that broke.**

Built for **Syndicate by Maximor**, hosted by **AO** — **Track 2: Autonomous Office of the CFO**.

Everyone automated the invoices that were never the problem. Tieout ignores the clean 87%,
picks up the exceptions, investigates each one across the ERP, the email thread and a vendor
portal that has no API, assembles an evidence pack with a proposed decision, escalates **once**
to a human — and learns the policy from that decision, so the next exception of the same kind
clears itself, citing the rule and the person who approved it.

---

## The problem

Accounts payable automation is a solved problem for invoices that match. The ones that do not
match are where the whole cost sits:

| what | figure | where it comes from |
|---|---|---|
| Share of an AP team's working time spent on exceptions | **60–70%** | zamp.ai |
| Time to investigate and resolve one exception | **45–60 minutes** | peakflo.co |
| Invoices that need manual rework | **12.5%** | Institute of Finance & Management, via Rossum |
| Invoices that fall into an exception loop | **30–40%** | zamp.ai |
| Payment delay an exception adds | **5–15 days** | peakflo.co |
| "Exceptions are the Achilles heel of AP automation" | — | Transcepta, citing APQC 2025 |

**How these were collected, honestly:** they were gathered on **2026-09-03** and recorded in
[`RESEARCH.md`](RESEARCH.md) with their publishers and that date. They are secondary
citations — the summaries name those publishers, and we did not re-open each publisher's own
page to re-verify the sentence. Treat them as the industry's stated figures, not as our
measurements. **Every number elsewhere in this README came out of a real run on this
machine**, and the command that produces it is printed next to it.

The insight the product is built on: **the 12.5% that break eat 60–70% of the team's time.**
Tieout works only those.

---

## The four beats

This is the demo, the test suite and the finish line, in the same order.

1. **Investigate.** A short-shipped invoice. Tieout reads the ERP, reads the vendor's email
   thread, and **signs into the vendor portal in a real browser to pull the delivery note** —
   because supplier portals do not have APIs. An evidence pack appears: every fact with its
   source, its link, the time it was read, whether code or the model read it, and a screenshot
   for anything read off the portal. A proposed decision, with a confidence.
2. **Decide once.** A human clicks Approve. A policy is created, **stamped with the approver's
   name and the date**.
3. **Clears itself.** The next short-ship exception is resolved with no human at all, citing
   that policy and that person. It does not sign in again — the portal session was saved.
4. **Refuses.** One exception where nothing lines up. Tieout says *"I am not confident. Here is
   everywhere I looked. You decide."* Refusing is a first-class outcome, not an error.

---

## How to run it

Every command below was run, exactly as written, on Windows 11 with Python 3.13 and Node 22
(the `git clone` excepted — this was written from inside the repo).

```bash
git clone https://github.com/rohit-jsfreaky/tieout.git
cd tieout

python -m pip install -e "backend[dev]"    # one project, one install
python -m playwright install chromium      # the portal beat opens a real browser

cp .env.example .env                       # then put a model key in it (see below)

tieout demo                                # the four beats, end to end, ~25 seconds
```

If your shell cannot find `tieout` after the install, its scripts directory is not on `PATH`;
`python -m tieout.cli demo` is the same command and always works.

`tieout demo` resets the world, runs all four beats and prints the counters it counted.
Nothing in that output is typed in.

### The same four beats, one command at a time

```bash
tieout reset                               # world + memory back to the seed
tieout world                               # ERP :8701, VendorLink :8702, AP mailbox :8703
tieout match                               # three-way match: 35 tie out, 5 do not
tieout work E1                             # beat 1 — ERP, inbox, portal, evidence pack
tieout decide E1 approve --by "Chris, Controller"   # beat 2 — the rule is born
tieout work E2                             # beat 3 — auto-cleared, citing the rule and Chris
tieout work E5                             # beat 4 — refused
tieout policies                            # every rule, every version, who approved it
tieout metrics                             # the counters
```

`tieout work` and `tieout demo` start the fake company themselves if it is not already running,
so `tieout world` in a second terminal is optional.

### The screen

```bash
python -m tieout.api                       # :8700 — starts the fake company too
cd desk && npm install && npm run dev      # :3000 (check the log — it moves if 3000 is taken)
```

Then, on the screen and nowhere else: **Work E1 → Approve → E2 → Work E2 → E5 → Work E5.**
`NEXT_PUBLIC_API_BASE` moves the API off `http://localhost:8700`.

### The tests

```bash
python -m pytest backend/tests -q          # 46 tests, ~60 s
python -m ruff check backend && python -m ruff format --check backend
cd desk && npm run typecheck && npm run lint && npm run build
```

The Python tests run **offline** — `conftest.py` empties `MODEL_API_KEY`, so every
reproducible part of the loop is proved without a model in the room. Fifteen of the 46 drive a
real Chromium against the real portal; they skip themselves, rather than fail, if Playwright's
browser is not installed.

The one that matters is `test_policy_loop.py`: approve E1 once, and E2 auto-clears citing
`SHORT-SHIP-01 v1` and Chris, Controller — asserted, not demonstrated.

### The model key

Tieout uses an LLM for exactly three small jobs and nothing else. It is a plain
OpenAI-compatible HTTP call, so any provider is a base-URL swap:

```
MODEL_BASE_URL=https://api.tensormux.com/v1
MODEL_API_KEY=your-key-here
MODEL_ID=glm-4-7-flash
```

TensorMux is the hackathon's inference partner ($5 free, no card); OpenRouter works with the
same three lines. **Without a key the demo still runs** — the model's three jobs degrade to
prose the code writes itself, and the trail says `read by code` instead of naming the model.

Verified by running `tieout demo` with the key removed. Identical either way: the exception
count, the human touches, the auto-clear, the refusal, the rule's id, version, condition,
action, approver, what it was learned from and what cited it. Different: the rule's
human-readable *name* and its rationale paragraph (code prose instead of model prose), and the
evidence count — **12 facts instead of 16**, because the model splits a vendor email into up to
three checkable claims where the code records the email verbatim as one. Nothing the loop
depends on is a model call.

---

## The agent workflow

```
   match ──▶ investigate ──▶ decide ──▶ escalate ──▶ learn ──┐
     ▲                                                       │
     └───────────────── the next one of that kind ◀──────────┘
                         clears itself, citing the rule
```

**Match.** `engine/match.py` runs a real three-way match — purchase order vs goods receipt vs
invoice — over the ERP's JSON API, and classes what broke: `short_ship`, `price_variance`,
`missing_po`, `unknown`. It never reads the seed's answer key, and
`test_the_engine_cannot_read_the_seed` scans every engine file to enforce that.

**Investigate.** `engine/investigate.py` walks three sources in order and stops the moment the
class's checklist is satisfied:

| source | file | what it does |
|---|---|---|
| ERP | `engine/sources/erp.py` | the invoice, the order, the receipt, the one candidate order |
| Inbox | `engine/sources/inbox.py` | finds the thread, and turns the vendor's own words into facts |
| Portal | `engine/sources/portal.py` | **the only Playwright importer.** Signs into VendorLink, reads the delivery note off the rendered page, screenshots it, and saves the session so the next investigation walks straight in |

**Decide.** `engine/decide.py`. Each class has a **written checklist**; each line passes or it
does not; **the confidence is the weight that passed.** No model produces a confidence anywhere
in this codebase. A judge can read the checklist and predict the number.

**Escalate — or refuse.** Below `CONFIDENCE_FLOOR = 0.70`, or with a named *required* check
failed, Tieout refuses and lists every place it looked, dead ends included.

**Learn.** `engine/policy.py`. One human decision becomes a rule with that human's name on it.

### What the model is allowed to do

`engine/model.py` is the only file in the project that calls an LLM, and it has exactly three
named jobs: turn email text into checkable facts, draft the rationale paragraph for a decision
**the code has already made**, and draft a candidate rule for `policy.py` to clamp.

**Matching, evidence collection, rule application and the confidence gate are deterministic
code.** That is what makes *"auto-cleared, citing SHORT-SHIP-01 v1, approved by Chris,
Controller"* reproducible when you rerun it, instead of a story the model told.

---

## Where the loop lives

### `backend/src/tieout/engine/policy.py` — the self-improving loop

The **only** file that creates, versions, matches and applies rules. Three functions:

```python
learn(pack, decision, approved_by)  -> Policy    a human decision becomes a rule
match(case, pack)                   -> Policy?   does an existing rule cover this one?
apply(policy, case, pack)           -> Decision  the rule clears it, citing the human
```

- **A rule is applied by code, never by a model.** The model may suggest a name and a
  tolerance; `policy.py` clamps every number before anything is stored — never narrower than
  the case it was learned from, never wider than the class ceiling — and always pins the rule
  to that supplier. The rule notes on itself when it narrowed the model's draft.
- **A rule never rescues a thin evidence pack.** `covers()` also requires the class's required
  check to pass, which is why the second short-ship refuses instead of clearing if the portal
  is switched off.
- **Nothing is ever deleted.** A decision that contradicts a rule produces a **new version**;
  the old version stays on the record, marked superseded, with the date it stopped applying.

Here is one, from a real run:

```
SHORT-SHIP-01 v1  [active]  Accept 5% short shipment variance
      when: class is short_ship; vendor is Northwind Industrial Supply; shortfall <= 5% of the
      billed quantity; exposure <= 185.00; evidence includes goods_receipt, delivery_note
      then: short_pay
      approved by Chris, Controller on 06 September 2026 · learned from E1 (INV-3036) ·
      drafted by model:glm-4-7-flash
      Controller approved a 5% variance for Northwind Industrial Supply, so the same tolerance
      applies to this vendor.
      cited by: E2
```

### `backend/src/tieout/engine/evidence.py` — the audit trail

The **only** writer of the trail. A fact that did not come through this file does not exist.
Every fact carries its `source`, its `locator` (the exact URL to fetch it again), the time it
was observed, the raw material it was read from, and — for anything off the portal — a
screenshot on disk. Three rules are enforced, not politely requested:

- a portal fact whose screenshot file is not on disk is **rejected**;
- a fact dated outside the open fiscal window is **rejected** — the model guessed the year
  `2024` on the very first test call we ever made, and a silently wrong year is exactly the bad
  evidence that must never reach a human;
- an empty statement, locator or raw body is **rejected**.

The trail also records the places Tieout looked and found **nothing**. Those dead ends are most
of why beat four is a considered refusal rather than a shrug.

---

## What improved across iterations

The counter is `human_touches`, and it is computed from the store — never hard-coded. One
approval is one touch; an auto-clear is zero.

**The measurement.** Two short-shipped invoices from the same supplier, INV-3036 and INV-3037.
Same world, same two invoices, run twice from a fresh `tieout reset`:

<table>
<tr><th></th><th>Before the loop</th><th>After one approval</th></tr>
<tr><td>commands</td>
<td><code>work E1</code><br><code>work E2</code></td>
<td><code>work E1</code><br><code>decide E1 approve --by "Chris, Controller"</code><br><code>work E2</code></td></tr>
<tr><td>Human touches</td><td>0 <i>(nothing decided yet)</i></td><td><b>1</b></td></tr>
<tr><td>Waiting on a person</td><td><b>2</b></td><td><b>0</b></td></tr>
<tr><td>Auto-cleared by a learned rule</td><td>0</td><td><b>1</b></td></tr>
<tr><td>Human touches avoided</td><td>0</td><td><b>1</b></td></tr>
<tr><td>Active policies</td><td>0</td><td>1</td></tr>
</table>

**Two exceptions that both needed a person, and now one of them does not** — and E2 is not
"skipped", it is *decided*: short-paid to the delivered quantity, citing `SHORT-SHIP-01 v1` and
Chris, Controller, with its own evidence pack behind it. Every later short-ship from that
supplier inside the tolerance costs zero touches. That is the loop:
**Learn → Run → Escalate → Improve.**

**The full demo, counted from the run** (`tieout demo`, identical across five consecutive runs
from a cold reset on 2026-09-06):

```
  Exceptions found                       5
  Worked                                 3
  Open, not yet worked                   2
  Human touches                          1
  Auto-cleared by a learned rule         1
  Human touches avoided                  1
  Refused (handed back)                  1
  Waiting on a person                    1
  Evidence items on the trail           16
  Screenshots                            3
  Active policies                        1
  Policy citations                       1
```

Three exceptions worked. One person was asked once. The second was **decided with no human at
all**. The fifth was handed back on purpose, which is the point of beat four. At the industry's
own 45–60 minutes per exception, that second one is 45–60 minutes nobody spent — and it is one
of an unbounded number, because the rule holds for every later short-ship from that supplier
inside the tolerance.

---

## Running this for real

The obvious question about the portal beat: **how does a browser log in on a server with no
screen?** Three tiers, and only the middle one is built this weekend.

1. **Service account.** IT provisions `tieout-bot@company.com` on the vendor portal with its
   own credentials, usually SSO-exempt and read-only. This is what enterprises actually do;
   RPA tools have worked this way in finance for fifteen years. **Most deployments never need a
   human to log in at all.**
2. **Session persistence.** ← **this is built.** After one successful sign-in,
   `sources/portal.py` saves the browser context with Playwright's `storage_state` to
   `~/.tieout/sessions/vendorlink.json`. The next investigation loads it and skips the login
   entirely. That is why beat 3 in the demo prints *"reused the saved VendorLink session — no
   sign-in needed"* where beat 1 printed *"signed in to VendorLink as ap-bot@kestrelmfg.com"*.
   "Logs in once" is demonstrable here, not hypothetical.
3. **Remote browser handoff, for SSO and 2FA.** *(Not built — that is a week, not a weekend.)*
   The browser runs on the server and its screen is streamed into the user's own tab (VNC in an
   iframe, or Chrome's screencast protocol; hosted-browser vendors sell this as a product). The
   user clicks a link, sees the real remote browser, signs in, does 2FA on their phone. The
   cookie is created on the server, where the agent needs it. Same experience as a bank's
   "connect your account" flow.

Related, and deliberate: **there is no Google/SSO button anywhere in this project.** The demo
portal uses a plain username-and-password form, which is what real B2B supplier portals
actually use. Credentials come from the environment only and are never written into an evidence
pack.

---

## What this does not do yet

Written plainly, because a judge will find these anyway.

- **The company is a fixture.** Kestrel Manufacturing Co., its eight suppliers, its 40
  invoices, its ERP, its VendorLink portal and its AP mailbox are all seeded by
  `backend/src/tieout/world/`. They are deliberately real *services* — the portal has a real
  form login and a real session cookie, so the engine's sign-in is genuine — but there is no
  NetSuite or SAP connector. `sources/erp.py` parses the ERP's JSON into its own DTOs and never
  imports the world, exactly as it would against a real system, and a test enforces that.
- **Three exception classes.** `short_ship`, `price_variance` and `missing_po`, plus `unknown`
  for the one that is meant to be unresolvable. A fourth class means a fourth checklist.
- **The rationale paragraph is model prose and varies between runs.** Nothing that has to be
  reproducible depends on it: the facts, the checklist, the confidence, the rule, the citation
  and every counter were byte-identical across five consecutive demo runs. The paragraph was
  not, and it is labelled with who wrote it.
- **One investigation at a time**, enforced with a `409`. The browser, the saved portal session
  and the screenshot folder are one shared resource; a second concurrent run would be a race,
  not a feature.
- **No user accounts, no permissions, no approval routing.** The approver is a name in a text
  field. In a real deployment that is an identity, and the rule should carry it.
- **Policies are learned per supplier.** A rule never widens itself to "any vendor" on its own.
  That is the conservative choice and it is intentional, but it does mean the loop pays off per
  supplier rather than instantly across the whole ledger.
- **No deployment.** Everything runs on localhost: the world on :8701–:8703, the API on :8700,
  the screen on :3000.
- **The AP statistics above are secondary citations**, as described in the problem section.

---

## How AO was used

The build ran as **one AO session per phase, each in its own git worktree and branch** — which
is AO's whole model: a session owns a worktree, the work happens there, and it merges back.

| session | phase | folder | what it produced |
|---|---|---|---|
| S1 | 1 · world | `backend/src/tieout/world/` | the fake company: seed, ERP, VendorLink portal, AP mailbox, one-command runner, `tieout reset`, 18 tests |
| S2 | 2 · engine | `backend/src/tieout/engine/` | the loop: three-way match, evidence, three sources, the confidence checklists, the refusal, the policy loop, `tieout demo` |
| S3 | 3 · api | `backend/src/tieout/api/` | routes and the SSE stream over the engine, and a background runner |
| S4 | 4 · desk | `desk/` | the one screen — and, on top of the plan, a live browser panel that shows the page the agent is reading |
| S5 | 5 · harden + ship | root | five cold demo runs, five passes through the screen, two bug fixes, this README |

Because the phases map onto separate modules, two sessions almost never touched the same file
even though `backend/` is a single Python project with a single `pyproject.toml`. The order of
the sessions is the dependency order: world → engine → api → desk.

Two things worth saying about the sessions rather than the tooling:

- **S4 rebuilt the desk's TypeScript types against the real `engine/models.py`.** The earlier
  skeleton had guessed them from the plan and got several wrong. Catching that is a session
  reading another session's merged output, which is the point of the worktree model.
- **S5 found two bugs that only repetition finds.** Driving the same four beats through the
  screen five times in a row surfaced both: the counter strip could read all zeros after Reset,
  because the desk asked for the counters in parallel with the queue — and it is the queue read
  that runs the match and fills the store; and the counters lagged a whole beat behind the
  screen, because a run was marked finished before its refetch landed. One pass through the
  demo would have shown neither. Both fixed in `desk/lib/useDesk.ts`.

---

## Repo map

```
backend/            ONE Python project. pyproject.toml, console script `tieout`.
  src/tieout/
    world/          the fake company — a fixture, not the product
    engine/         THE LOOP
      match.py        the real three-way match
      evidence.py     ← the only writer of the audit trail
      policy.py       ← the only file that creates, versions and applies rules
      decide.py       the checklists, the confidence, the refusal
      model.py        the only LLM caller. three named jobs.
      sources/        erp.py · inbox.py · portal.py (the only Playwright importer)
    api/            thin FastAPI + SSE. no logic.
    cli.py          the only thing that prints
  tests/            46 tests; fifteen drive a real Chromium against the real portal
desk/               the one screen. Next.js 16, TypeScript strict, Tailwind v4.
.env.example        every setting, with what it is for
MASTER-PLAN.md      phases, finish lines, hour budget
RESEARCH.md         verified facts, each with a date and a source
PROGRESS.md         live state
```

## Licence

MIT.
