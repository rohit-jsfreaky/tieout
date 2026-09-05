# PROGRESS — Tieout (root live state)

> Read this first, every session. Update it before ending the session.
> Per-folder detail: `backend/PROGRESS.md`, `desk/PROGRESS.md`.

## Current state — 2026-09-05

- **Phase 1 (world) is DONE.** Its finish line passes: one command starts the ERP (:8701),
  the VendorLink portal (:8702) and the AP inbox (:8703); `curl :8701/invoices` returns 40;
  a real browser signs into the portal and reads "95" off delivery note DN-1042;
  `tieout reset` puts the world back to the seed. 18 tests green, ruff clean.
  Detail in `backend/PROGRESS.md`.
- **Next:** Phase 2 (`engine`) in AO session S2 — `tieout match` must find exactly the five
  seeded exceptions and class them, without reading the seed's own exception table.

## Before the window — 2026-09-03

- **Current phase:** 0 (Setup). Build window opens **Sep 5, 21:30 IST**.
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

- **2026-09-03** — event researched, idea picked, Discord read, scaffold + plans written.
- **2026-09-04** — structure simplified to TWO folders: `backend/` (one Python project with
  world/engine/api modules) and `desk/`. Was three separate Python projects; now one
  pyproject, one venv, one install. Phases and finish lines unchanged.
  AO v0.12.10 confirmed (Windows .exe, 126 MB). TensorMux (sponsor) gives $5 free with no
  card and is OpenAI-compatible — use it as the model provider, OpenRouter $3 as backup.
- **2026-09-04 (later)** — TensorMux signed up with Google, API key created and stored in
  `.env` (gitignored, Rohit rotates after). $5/$5 credit verified, expires Sep 18. Only one
  model live: `gemma-4-31b`. Rate limits 15 rpm / 20k tpm. First real call passed and exposed
  two gotchas now written into RESEARCH.md: the model fences its JSON, and it guessed the
  wrong YEAR for a date — both would have poisoned the evidence trail silently.
- **2026-09-05 (S1, `world`)** — Phase 1 built inside the window: seed + ERP + portal + inbox
  + one-command runner + `tieout reset`, 18 tests. The fake company is Kestrel Manufacturing
  Co. buying from 8 suppliers; 40 invoices, 35 clean, 5 broken on purpose. The portal is one
  supplier network with a real form login and a session cookie, so the engine's Phase 2
  sign-in is genuine. Verified with curl and with a real Chromium, not only in tests.
