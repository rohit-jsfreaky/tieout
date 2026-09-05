# RESEARCH — verified facts only

Every entry has a **date** and a **source** (the page actually opened). Missing fact → open the
real docs with Playwright MCP, add it here. Never WebSearch. Never build on a guess.

## The event (Notion + Luma + Discord, 2026-09-03)

- Syndicate by Maximor, hosted by AO. Sep 5 21:30 IST → Sep 7 03:30 IST. Online.
- Track 2 = "Autonomous Office of the CFO": "automate a real workflow handled by a company's
  accounting, finance, or treasury team ... take over a repetitive internal finance process end
  to end, **including exceptions and human review**." Internal finance ops only — not consumer
  banking, trading, lending, payments.
- Per track: 1st $1,000 cash + $1,000 Dodo credits · 2nd $500 + $500 · 20 × $100 AI Grants
  India credits. Internships with Maximor (NYC or remote, paid, convertible) and AO — selection
  by "project scoring, presentation etc", not placing.
- Must use AO throughout; video must show AO usage; they count sessions.
- Submit in Discord `#syndicate-project-showcase`. Public repo + video + README required.

## Judge intel (Discord `#syndicate-general` / `#syndicate-help`, 2026-09-03, verbatim)

- Maaz: "Rayed has won 22 hackathons in the past"
- Rayed | Maximor: "what's most important is the actual self-improving loop and how the agent
  is engineered. I'd say to have a better focus, stick with one domain"
- Rayed: "demonstrating one domain really well also works"
- Rayed on internships: "selective people will get interviewed ... it depends on our project
  scoring, presentation etc"
- Nobody in any Syndicate channel has announced a project idea as of 2026-09-03 evening.

## Maximor (maximor.ai + Google, 2026-09-03)

- "Autonomous finance platform for the office of the CFO." $9M seed (TechCrunch). Founders
  Ramnandan Krishnamurthy, Ajay Krishna Amudan (ex-Microsoft). Backers: Foundation Capital,
  Gaia, BoldCap, Aravind Srinivas.
- Homepage loop: **01 Learns → 02 Runs → 03 Escalates → 04 Improves**. "REVERSE ENGINEERING"
  policy from Bank feed / Excel / NetSuite / SAP. Example policy that versions itself:
  `SHORT-PAY-01 · short ≤ $50 → auto-close` → `v2 · ≤ $50 or ≤ 5% freight — UPDATED`.
  Caption: "EVERY CLOSE, SMARTER."
- Trademark: **"Audit-Ready Agents™"**. Promises "full audit trail attached", "brings you in
  when judgment is needed". Their stated core problem: the **trust gap**.
- "No rip-and-replace, no migration. On top of your ERP." Integrations named: NetSuite, SAP,
  Intacct, Salesforce, banks, payroll — **all API-shaped. Portals with no API are the residue.**

## The AP exception numbers (Google AI Overview citing peakflo.co, zamp.ai, Rossum/IOFM,
Transcepta/APQC 2025 — 2026-09-03). Re-open the primary sources before quoting in the README.

- 45-60 minutes to investigate and resolve each invoice exception (peakflo.co)
- AP teams spend 60-70% of working time on exceptions (zamp.ai)
- 30-40% of invoices fall into exception loops
- 12.5% of all invoices need manual rework (Institute of Finance & Management, via Rossum)
- 5-10 minutes just to find a missing PO number
- Exceptions add 5-15 days of payment delay
- "Exceptions are the Achilles heel of AP automation" (Transcepta, citing APQC 2025)
- Common causes: PO/receipt/invoice mismatch (3-way match), missing PO, non-PO "maverick
  spend", data-entry errors

## AO — Agent Orchestrator (aoagents.dev/docs + GitHub README + X, 2026-09-03)

- Desktop IDE for supervising coding agents. Go daemon on 127.0.0.1, local API, optional CLI.
- Each session = its own git worktree + branch; PR, CI, review state attached to the session.
- Harnesses: Claude Code, Codex, OpenCode, Droid. Chat UI or native terminal UI per session.
- Windows build: `agent-orchestrator-win32-x64.exe` from GitHub releases. Apache-2.0.
- Self-description on X: "Agent IDE + meta-harness for orchestrating parallel coding agents
  with built-in loops and full control." 10k+ stars, ~90 contributors.
- Basic loop: add project → start session → isolated worktree → pull request → CI/review →
  merge → cleanup.

## Neatlogs (neatlogs.com, 2026-09-03)

Agent observability: traces with tool calls, timing, cost; threaded comments; an AI that
explains why an agent picked the wrong tool. Founder @Ajay | Neatlogs is in the Discord.
Optional for us — a trace of one investigation in the video would be a nice touch, not a
requirement. A student could not log in with a personal email (Discord, unresolved).

## Versions (verified on PyPI/npm 2026-08-31 during the Cairn build — re-check on Phase 0)

playwright 1.62.0 · fastapi 0.141.1 · next 16.3.3 · @phosphor-icons/react 2.1.10

## Hard-won notes from the Cairn build (same stack, 2026-09-01..03)

- `create-next-app@latest` pinned a `next` version that was not published; `package.json` had
  to be corrected by hand to 16.3.3. Check the version it writes.
- **Next 16 has breaking changes vs training data.** `next dev` writes an agent-rules block
  into the folder's CLAUDE.md pointing at `node_modules/next/dist/docs/`. Read those docs
  before writing any Next code. Tailwind is v4.3 — wire it the way the current docs say.
- Playwright's sync API refuses to run inside an asyncio loop and binds objects to the
  creating thread. Under FastAPI, run the browser on its own thread (or use the async API).
- Assert the user-visible outcome in tests, not the internal event — a green test proved a
  download "fired" while the file was deleted on context close.
- Never store a password in any stored artefact; resolve secrets from env at run time.

## Finance notes (fill in Phase 0 — five lines is enough)

- 3-way match:
- Short-ship:
- Price variance / tolerance:
- Non-PO invoice:
- What "short-pay" means:

## Model provider — decided 2026-09-04

The engine needs an LLM for exactly three small jobs: read an email into Facts, draft the
one-paragraph rationale, and draft a rule from a human decision. Everything else is
deterministic code. Volume is tiny: ~5k tokens for a full 5-exception demo run.

**Use TensorMux — the hackathon's own Inference Partner.** tensormux.com, verified 2026-09-04:
> "We're burning our GPUs so you can build free — **$5 credit, no card**."
> "Try our free shared endpoint" · works with the **OpenAI SDK** · now in the NVIDIA Inception
> Program · v1.0 of the open-source gateway is live.

OpenAI-compatible means `model.py` is a plain HTTP call and swapping provider is one env var.
Keep Rohit's **$3 OpenRouter key as the backup**. Combined that is ~$8 against a need of well
under $1 — funding is not a risk. Ask in `#syndicate-help` whether participants get more
TensorMux credit; using the inference partner is also a small goodwill point with the hosts.

### Account created and TESTED 2026-09-04 — it works

Signed up with Google (rohitkashyapmrt@gmail.com). Values are in `.env` (gitignored).
Rohit will rotate the key after the event.

```
MODEL_BASE_URL = https://api.tensormux.com/v1
MODEL_ID       = gemma-4-31b
```

- **Only ONE model is live on the shared endpoint: `gemma-4-31b`** (Google Gemma 4 31B
  Instruct). Served by vLLM (`system_fingerprint: vllm-0.25.1`). Listed as "coming soon to
  shared / available on dedicated": DeepSeek V4 Pro, GLM-5.2, Kimi K2.6, MiniMax M3,
  Nemotron 3 Ultra, Mistral Medium 3.5, MiMo V2.5 Pro. **Do not plan around those.**
- **Free credit confirmed on the Usage page: $5.00 / $5.00, 0% used, 1,000,000 tokens.**
  ⏳ **EXPIRES 2026-09-18** (14 days). Fine — the hackathon ends Sep 7.
- **Rate limits: 15 requests/minute, 20,000 tokens/minute.** Tight enough to matter. The
  engine investigates exceptions one at a time, so this is fine, but do NOT fan out parallel
  LLM calls across all 5 exceptions at once, and add a retry-with-backoff on 429.
- Free tier allows **one API key per account**.
- Live test returned HTTP 200 and the right answer, using 113 total tokens:
  prompt "we shipped 95 of the 100 units on Sep 2" -> `{"shipped": 95, "ordered": 100}`.

### ⚠️ THE MODEL CHANGED MID-BUILD — `glm-4-7-flash` is now the ONLY one (2026-09-05 23:30)

`gemma-4-31b` was **removed by TensorMux during the build window**. It now returns
`model_not_found` (HTTP 400) and `GET /v1/models` lists exactly one model: `glm-4-7-flash`.
Found because Rohit noticed their console only showed glm and asked us to check instead of
trusting the note we had written two hours earlier. Lesson: re-verify a provider's model list
before depending on it, not once at setup.

`MODEL_ID` and a new `MODEL_MAX_TOKENS=800` are set in `.env`. Verified working after the
switch: correct answer, correct year, `finish_reason: stop`, 337 completion tokens.

### `glm-4-7-flash` is a REASONING model — this is now mandatory, not optional

Offered by TensorMux in the Discord. Tested on the same fact-extraction prompt. It works, but
it is a **reasoning model** and that changes how it must be called:

- It writes its thinking into a separate **`reasoning`** field and leaves **`content` EMPTY**
  until the thinking finishes. At `max_tokens=150` it returned `content: None`, HTTP 200, no
  error, 150 completion tokens burned. **A silent empty answer is the worst failure mode we
  could have** — the engine would record a Fact with nothing in it.
- At `max_tokens=800` it answered correctly, and got the year right (2026-09-02) once the
  prompt carried today's date.
- Cost: **299 completion tokens** for the job gemma does in **39**. Roughly 7x. With a
  20,000 tokens/minute rate limit that matters.
- It still wraps JSON in a ``` fence, same as gemma.

**Decision (forced): `glm-4-7-flash`, `max_tokens` 800.** gemma no longer exists, so the
reasoning-model handling is REQUIRED, not a nice-to-have:
- `max_tokens` >= 600 on every call, from `MODEL_MAX_TOKENS` in `.env`
- an empty `content` MUST raise, never be recorded as an empty answer
- budget ~340 completion tokens per call; with a 20,000 tokens/minute limit that is roughly
  55 calls per minute of headroom, and investigations run one at a time, so it is fine
- the `reasoning` field is useful for debugging but must never be stored as a Fact

### TWO GOTCHAS found in that very first call — both would corrupt evidence silently

1. **It wraps JSON in a markdown code fence.** The reply was ```` ```json
{...}
``` ````,
   not bare JSON. `model.py` must strip fences before `json.loads`, or every fact extraction
   fails. Do not assume clean JSON.
2. **It invented the year.** Asked for `ship_date` from "shipped on Sep 2", it answered
   **`2024-09-02`** — the model's own default, not our world's date. In a finance product a
   silently wrong year is exactly the kind of bad evidence that must never reach a human.
   **Every prompt that touches a date must state today's date explicitly**, and `evidence.py`
   should reject a Fact whose date falls outside the fiscal window it was told about.

## AO gives NO model credits (aoagents.dev/docs/faq, verbatim, 2026-09-04)

> **"What does AO cost?"** — "AO is Apache-2.0 licensed. **Agent usage is billed according to
> the provider account or subscription used by each installed harness.** Chat records usage
> data when the provider reports it."

> **"Do I have to use Claude Code?"** — "No. AO includes adapters for **more than twenty
> harnesses**, including Claude Code, Codex, Cursor, Aider, OpenCode, Droid, Kimi Code... Native
> Chat currently supports installed Codex, Claude Code, OpenCode, and Droid; other harnesses use
> Terminal UI."

So AO is a free wrapper. It ships no models and no credits — it launches the coding agent
already installed on the machine, on that agent's own subscription. Rohit has Claude Code, so
AO runs Claude Code and costs nothing extra.

**Two different AI costs, do not confuse them:**
1. The AI that WRITES the code = Claude Code through AO = his existing subscription = ₹0 extra.
2. The AI INSIDE Tieout (reading emails into facts) = TensorMux/OpenRouter = well under $1.

Other FAQ facts: Windows is fully supported ("desktop app, Chat, and native Terminal UI through
AO's conpty host"). Data lives under `~/.ao` (SQLite in `~/.ao/data`, plus managed worktrees).
The daemon is unauthenticated and fixed to 127.0.0.1 — never expose it. One session commits to
one controller at a time (Chat or Terminal, not both). The legacy npm package `@aoagents/ao` is
frozen at 0.10.0 — use the desktop download.

## AO release (verified via the GitHub API, 2026-09-04)

Latest **v0.12.10**, published 2026-08-31. Windows asset: `agent-orchestrator-win32-x64.exe`,
126 MB. Direct link:
`https://github.com/Untrivial-ai/agent-orchestrator/releases/latest/download/agent-orchestrator-win32-x64.exe`

## OPEN QUESTIONS

1. TensorMux model id + base URL (record above once the free endpoint is live for us).
2. AO on Windows with this two-folder repo — confirmed in the practice session?
3. Do the AP statistics' primary pages still say what the AI Overview summarised? Open two of
   them before the README quotes numbers.
4. Do Syndicate participants get extra TensorMux credit? Ask in `#syndicate-help`.
