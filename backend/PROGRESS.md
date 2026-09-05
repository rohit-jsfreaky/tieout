# PROGRESS — backend/

> Working memory for this folder. Read first, update before ending every session.

## Current state — 2026-09-04

- Phases 1-3 not started. Build window opens **Sep 5, 21:30 IST**. No code before then.
- Plan locked in `PLAN.md`. Architecture boundaries locked in `CLAUDE.md`.
- **Restructured 2026-09-04:** `world/`, `engine/` and `api/` used to be three separate
  top-level Python projects. Merged into ONE project with three modules — one pyproject, one
  venv, one install. Rohit asked whether the build was really just a backend and a frontend;
  it is, and the folders now say so. Phases and finish lines are unchanged.

## Done

(nothing yet)

## Next action

Phase 1, step 1a in `PLAN.md`, inside AO session S1, at 21:30 IST Saturday.

## Decisions made

- One Python project, three modules (`world`, `engine`, `api`). Not three packages.
- Rule application is deterministic code, never an LLM call. Reproducibility is the point.
- Refusing is a first-class outcome with its own demo beat.
- `policy.py` and `evidence.py` are single-owner files, so a judge finds the loop and the
  audit trail in under a minute.
- LLM access is a plain OpenAI-compatible HTTP call. TensorMux and OpenRouter differ only by
  base URL, so switching providers mid-build costs nothing.

## Blockers

- Model base URL / key / id not chosen yet (Phase 0 — record in `../RESEARCH.md`).

## Session log

- **2026-09-03** — folders created, plans written. No code.
- **2026-09-04** — merged into a single backend project.
